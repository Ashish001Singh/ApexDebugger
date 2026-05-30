from typing import Callable
from src.apex_copilot.reasoning.models import Finding

from .soql_in_loop import check_soql_in_loop
from .dml_in_loop import check_dml_in_loop
from .hardcoded_id import check_hardcoded_id
from .missing_crud_fls import check_missing_crud_fls

RuleFunc = Callable[[str], list[Finding]]

RULES: list[RuleFunc] = [
    check_soql_in_loop,
    check_dml_in_loop,
    check_hardcoded_id,
    check_missing_crud_fls,
]


def run_all_rules(code: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        findings.extend(rule(code))
    return findings
