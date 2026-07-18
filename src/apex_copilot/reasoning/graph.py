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

But you should also take care of the findings which is already feed into you you should never check those again
"""
from src.apex_copilot.reasoning.models import Finding, ReviewResult, LLMReviewOutput
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from config import settings
from openai import OpenAI

client = OpenAI(api_key=settings.openai_api_key)


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
        findings=findings,
        summary=final_state["summary"],
        llm_explanation=final_state["llm_explanation"],
    )


def retrieve_context(state: ApexReviewState) ->dict:
  return {"context_chunks": []}


def reason(state: ApexReviewState) -> dict:
  user_message = f"""Review this Apex code.

Filename: {state['filename']}
Code:
{state['code']}

Explain why each matters and rate overall risk."""

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

  return{
        "summary":output.summary,
        "llm_explanation": "\n".join(f" - [line {f.line}] {f.rule.value}: {f.message}"  for f in output.findings)
  }


builder = StateGraph(ApexReviewState)
builder.add_node("reason", reason)
builder.add_node("retrieve_context", retrieve_context)
builder.add_edge(START, "retrieve_context")
builder.add_edge("retrieve_context","reason")
builder.add_edge("reason",END)

graph = builder.compile()