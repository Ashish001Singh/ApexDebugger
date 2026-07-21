from typing import Callable
from src.review_core.models import Finding
from .unsafe_inner_html import check_unsafe_inner_html

RuleFunc = Callable[[str, str], list[Finding]]
RULES: list[RuleFunc] = [
    check_unsafe_inner_html,
]

def run_all_rules(js_code: str, html_code: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        findings.extend(rule(js_code, html_code))
    return findings