"""
Phase 2 stub: LangGraph graph for reasoning over rule findings.

TODO (Phase 2):
  - Install langgraph: `uv add langgraph`
  - Nodes: retrieve_context → apply_rules → llm_reason → merge_output
  - State: ApexReviewState(code, findings, context_chunks, llm_output)
  - Edge: always sequential for now, add conditional edges in Phase 3
"""
from src.apex_copilot.reasoning.models import Finding, ReviewResult


def run_reasoning_graph(code: str, findings: list[Finding], filename: str) -> ReviewResult:
    """
    Phase 2: call LangGraph graph to enrich findings with LLM explanation.
    Phase 1: pass-through — returns findings unchanged.
    """
    # TODO (Phase 2): replace with actual graph execution
    return ReviewResult(
        filename=filename,
        findings=findings,
        summary=None,
        llm_explanation=None,
    )
