from src.lwc_copilot.rules.registry import run_all_rules
from src.lwc_copilot.reasoning.graph import run_reasoning_graph
from src.review_core.models import ReviewResult


def review(js_code: str, html_code: str = "", filename: str = "anonymous.js") -> ReviewResult:
    findings = run_all_rules(js_code, html_code)
    result = run_reasoning_graph(js_code, html_code, findings, filename)
    return result