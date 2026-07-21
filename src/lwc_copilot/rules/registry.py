from typing import Callable
from src.review_core.models import Finding
from .unsafe_inner_html import check_unsafe_inner_html
from .manual_dom_manipulation import check_manual_dom_manipulation

RuleFunc = Callable[[str, str], list[Finding]]
RULES: list[RuleFunc] = [
    check_unsafe_inner_html,
    check_manual_dom_manipulation
]

def run_all_rules(js_code: str, html_code: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        findings.extend(rule(js_code, html_code))
    return findings