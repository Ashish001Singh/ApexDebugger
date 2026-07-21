from typing import Callable
from src.review_core.models import Finding
from .unsafe_inner_html import check_unsafe_inner_html
from .manual_dom_manipulation import check_manual_dom_manipulation
from .imperative_apex_no_error_handling import check_imperative_apex_no_error_handling
from .missing_wire_error_handler import check_missing_wire_error_handler

RuleFunc = Callable[[str, str], list[Finding]]
RULES: list[RuleFunc] = [
    check_unsafe_inner_html,
    check_manual_dom_manipulation,
    check_imperative_apex_no_error_handling,
    check_missing_wire_error_handler,
]

def run_all_rules(js_code: str, html_code: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        findings.extend(rule(js_code, html_code))
    return findings