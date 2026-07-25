"""
Phase 2 stub: LangGraph graph for reasoning over rule findings.

TODO (Phase 2):
  - Install langgraph: `uv add langgraph`
  - Nodes: retrieve_context → apply_rules → llm_reason → merge_output
  - State: ApexReviewState(code, findings, context_chunks, llm_output)
  - Edge: always sequential for now, add conditional edges in Phase 3
"""
SYSTEM_PROMPT = """
You are a Salesforce Certified Technical Architect (CTA) with 15+ years of experience designing, reviewing, and optimizing enterprise Salesforce Lightning Web Components (LWC).

Your task is to perform a professional code review of the provided JavaScript, HTML, and CSS files.

Follow these guidelines:

1. Follow Salesforce official best practices, LWC Developer Guide, and Lightning Web Security (LWS) recommendations.
2. Detect only genuine issues and avoid false positives.
3. Review the code from the perspectives of security, performance, maintainability, scalability, readability, and reliability.
4. Validate LWC-specific best practices such as @wire usage, imperative Apex calls, lifecycle hooks, reactive properties, template directives, event handling, and rendering.
5. Ensure proper error handling for all imperative Apex calls and asynchronous operations.
6. Verify efficient Apex interaction, caching, and governor limit awareness.
7. Identify security risks including XSS, unsafe DOM manipulation, insecure navigation, and improper data access.
8. Recommend declarative and reactive solutions over imperative implementations whenever possible.
9. Do not report stylistic or formatting issues unless they impact functionality or maintainability.
10. Avoid duplicate findings for the same issue.
11. Provide concise, actionable recommendations that align with Salesforce best practices.
12. Do not flag Salesforce-supported patterns unless they are implemented incorrectly.

Make sure to check the line clearly and don't deflect from the actual line because we are merging all the findings together so
it is very important that line should be considered clearly.

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
# Two rules were retired from the regex layer to the LLM after ASCENT spot-checks
# showed high false-positive rates driven by judgment the regex couldn't make:
#   - imperative_apex_no_error_handling: promise-chain error handling needs
#     balanced-delimiter parsing (beyond regex).
#   - missing_wire_error_handler: distinguishing data wires that need a handler
#     from error-less context adapters is an open-ended allowlist problem.
# Both are LLM-owned now. The regex layer keeps only syntactically-certain rules.
REGEX_OWNED = {
    RuleId.unsafe_inner_html, RuleId.manual_dom_manipulation,
    RuleId.apex_call_in_loop,
}

client = OpenAI(api_key=settings.openai_api_key)

# Consensus voting: run the LLM VOTE_RUNS times, keep findings appearing in
# >= VOTE_THRESHOLD runs. 3/2 is the cheapest meaningful majority.
VOTE_RUNS = 3
VOTE_THRESHOLD = 2


class LWCReviewState(TypedDict):
  js_code:str
  html_code:str
  filename: str
  findings: list[Finding]
  context_chunks: list[str]   #
  summary: str | None
  llm_explanation: str | None



def run_reasoning_graph(js_code: str, html_code:str, findings: list[Finding], filename: str) -> ReviewResult:
    """
    Phase 2: call LangGraph graph to enrich findings with LLM explanation.
    Phase 1: pass-through — returns findings unchanged.
    """
    # TODO (Phase 2): replace with actual graph execution
    initial_state = {
        "js_code": js_code,
        "html_code": html_code,
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

_KB_PATH = Path(__file__).parent.parent / "kb" / "best_practices.md"

def retrieve_context(state: LWCReviewState) -> dict:
    chunks = []
    if _KB_PATH.exists():
        chunks.append(_KB_PATH.read_text())
    user_path = settings.user_best_practices_path
    if user_path and Path(user_path).exists():
        chunks.append(Path(user_path).read_text())
    return {"context_chunks": chunks}




def reason(state: LWCReviewState) -> dict:
  grounding = ""
  
  if state["context_chunks"]:
      joined = "\n\n".join(state["context_chunks"])
      grounding = (
          "\n\nReference — Salesforce best practices. Ground your findings in these; "
          "do not contradict them:\n" + joined + "\n"
      )

  user_message = f"""Review this Lightning Web component.

Filename: {state['filename']}
JavaScript:
{state['js_code']}
Template HTML:
{state['html_code']}
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


builder = StateGraph(LWCReviewState)
builder.add_node("reason", reason)
builder.add_node("retrieve_context", retrieve_context)
builder.add_edge(START, "retrieve_context")
builder.add_edge("retrieve_context", "reason")
builder.add_edge("reason",END)

graph = builder.compile()

