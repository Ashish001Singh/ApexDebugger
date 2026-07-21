"""
Phase 2 stub: LangGraph graph for reasoning over rule findings.

TODO (Phase 2):
  - Install langgraph: `uv add langgraph`
  - Nodes: retrieve_context → apply_rules → llm_reason → merge_output
  - State: ApexReviewState(code, findings, context_chunks, llm_output)
  - Edge: always sequential for now, add conditional edges in Phase 3
"""
SYSTEM_PROMPT = f"""
You are a 15 year salesforce Architect with a strong background in Salesforce
Development. Your job is to check the code, the classes, the method, static variables.
In Apex class you check for:
1. If the class or any method has cyclomatic complexity greater than 40 for class and 25 for method you just flag it as a medium issue.
2. If the same method is written twice.
3. If we can combine different calls tto database or not
4. If we SOQL or DML has the user permission given to it while performing the operation
5. If some variable is there which is being used multiple times in the whole class we should put in the static variable
6. If the code written adheres to the best practices of salesforce or not
7. if there is something which can result in heap size or out of bound or null pointer exception or any kind of exception you should flag that as well

Make sure to check the line clearly and don't deflect from the actual line because we are merging all the findings together so
it is very important that line should be considered clearly.

Do NOT report missing CRUD/FLS if an isAccessible/isCreateable check exists.
Do NOT report a loop that isn't present. Do NOT report missing sharing if
'with sharing' is declared. Only report what you can point to a specific line for.
"""
from src.review_core.models import Finding, ReviewResult, LLMReviewOutput
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from config import settings
from openai import OpenAI
from src.review_core.models import RuleId  # if not already imported
from src.review_core.merging import merge_findings
from src.review_core.voting import vote_findings

# Rules the deterministic layer owns — regex is authoritative. The LLM's job is
# only the reasoning rules regex CAN'T do; drop its claims on regex-owned rules.
REGEX_OWNED = {
    RuleId.soql_in_loop, RuleId.dml_in_loop, RuleId.hardcoded_id,
    RuleId.hardcoded_external_id, RuleId.missing_crud_fls,
    RuleId.missing_sharing_declaration, RuleId.explicit_system_mode,
    RuleId.nested_loop_2, RuleId.nested_loop_deep,
}

client = OpenAI(api_key=settings.openai_api_key)

# Consensus voting: run the LLM VOTE_RUNS times, keep findings appearing in
# >= VOTE_THRESHOLD runs. 3/2 is the cheapest meaningful majority.
VOTE_RUNS = 3
VOTE_THRESHOLD = 2


class ApexReviewState(TypedDict):
  code:str
  filename: str
  findings: list[Finding]
  context_chunks: list[str]
  summary: str | None
  llm_explanation: str | None



def run_reasoning_graph(code: str, findings: list[Finding], filename: str) -> ReviewResult:
    """
    Phase 2: call LangGraph graph to enrich findings with LLM explanation.
    Phase 1: pass-through — returns findings unchanged.
    """
    # TODO (Phase 2): replace with actual graph execution
    initial_state = {
        "code": code,
        "filename": filename,
        "findings": findings,
        "context_chunks": [],
        "summary": None,
        "llm_explanation": None,
    }
    final_state = graph.invoke(initial_state)

    print('summary: '+final_state["summary"])
    print('llm_explanation: '+final_state["llm_explanation"])

    return ReviewResult(
        filename=filename,
        findings=final_state["findings"],
        summary=final_state["summary"],
        llm_explanation=final_state["llm_explanation"],
    )

from pathlib import Path

# Small-corpus RAG: the whole best-practices doc is loaded and stuffed into the
# prompt (no embeddings / vector DB until the corpus outgrows the context window).
_KB_PATH = Path(__file__).parent.parent / "kb" / "best_practices.md"


def retrieve_context(state: ApexReviewState) -> dict:
  chunks = []
  if _KB_PATH.exists():
      chunks.append(_KB_PATH.read_text())
  # Optional project-specific best practices supplied by the user.
  user_path = settings.user_best_practices_path
  if user_path and Path(user_path).exists():
      chunks.append(Path(user_path).read_text())
  return {"context_chunks": chunks}



def reason(state: ApexReviewState) -> dict:
  grounding = ""
  if state["context_chunks"]:
      joined = "\n\n".join(state["context_chunks"])
      grounding = (
          "\n\nReference — Salesforce best practices. Ground your findings in these; "
          "do not contradict them:\n" + joined + "\n"
      )

  user_message = f"""Review this Apex code.

Filename: {state['filename']}
Code:
{state['code']}
{grounding}
Explain why each matters and rate overall risk."""



  runs = []
  summary = None
  for _ in range(VOTE_RUNS):
      response = client.chat.completions.parse(
          model=settings.openai_model,
          max_tokens=1024,
          messages=[
              {"role": "system", "content": SYSTEM_PROMPT},
              {"role": "user", "content": user_message},
          ],
          response_format=LLMReviewOutput,
      )
      output = response.choices[0].message.parsed
      runs.append(output.findings)
      if summary is None:
          summary = output.summary

  voted = vote_findings(runs, VOTE_THRESHOLD)
  merged_findings = merge_findings(state["findings"], voted, REGEX_OWNED)
  return{
        "findings": merged_findings,
        "summary": summary,
        "llm_explanation": "\n".join(f" - [line {f.line}] {f.rule.value}: {f.message}"  for f in merged_findings)
  }


builder = StateGraph(ApexReviewState)
builder.add_node("reason", reason)
builder.add_node("retrieve_context", retrieve_context)
builder.add_edge(START, "retrieve_context")
builder.add_edge("retrieve_context","reason")
builder.add_edge("reason",END)

graph = builder.compile()

