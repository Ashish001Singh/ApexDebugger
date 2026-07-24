import re
from src.review_core.models import Finding, RuleId, Severity

_WIRE_DECORATOR = re.compile(r"@wire\([^)]*\)\s*\n?\s*(\w+)\s*(\(([^)]*)\))?\s*[;{]")


def check_missing_wire_error_handler(js_code: str, html_code: str) -> list[Finding]:
    findings: list[Finding] = []
    for match in _WIRE_DECORATOR.finditer(js_code):
        params = match.group(3)
        if params is not None and "error" in params:
            continue
        lineno = js_code[:match.start()].count("\n") + 1
        findings.append(
                Finding(
                    rule=RuleId.missing_wire_error_handler.value,          # <- fill: which RuleId member?
                    severity=Severity.MEDIUM,      # <- fill: Severity.HIGH
                    line=lineno,
                    message="@wire has no error handling — a failed Apex/wire adapter call fails silently.",
                    suggestion="Wire to a function with ({ data, error }) params and handle the error branch, instead of a bare @wire property.",
                )
            )
    return findings