from typing import Callable
from src.review_core.models import Finding

RuleFunc = Callable[[str, str], list[Finding]]
RULES: list[RuleFunc] = []

def run_all_rules(js_code: str, html_code: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        findings.extend(rule(js_code, html_code))
    return findings