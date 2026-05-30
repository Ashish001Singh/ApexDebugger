from src.apex_copilot.rules import run_all_rules
from src.apex_copilot.reasoning.graph import run_reasoning_graph
from src.apex_copilot.reasoning.models import ReviewResult


def review(code: str, filename: str = "anonymous.cls") -> ReviewResult:
    """
    Main entrypoint. Takes raw Apex source, returns structured ReviewResult.

    Phase 1: deterministic rules only.
    Phase 2: adds LangGraph + Claude reasoning.
    Phase 3: adds KB retrieval context.
    """
    findings = run_all_rules(code)
    result = run_reasoning_graph(code, findings, filename)
    return result
