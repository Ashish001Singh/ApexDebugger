import re
from src.review_core.models import Finding, RuleId, Severity

_MANUAL_DOM_MANIPULATION = re.compile(r'lwc:dom\s*=\s*"manual"')

def check_manual_dom_manipulation(js_code: str, html_code: str) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(html_code.splitlines(), start=1):
        if _MANUAL_DOM_MANIPULATION.search(line):
            findings.append(
                Finding(
                    rule=RuleId.manual_dom_manipulation.value,          # <- fill: which RuleId member?
                    severity=Severity.MEDIUM,      # <- fill: Severity.HIGH
                    line=lineno,
                    message="Component uses 'lwc:dom=\"manual\"', which bypasses LWC's rendering lifecycle.",
                    suggestion="Review whether manual DOM management is necessary. Prefer declarative templates and reactive state. Reserve 'lwc:dom=\"manual\"' for approved third-party library integrations or scenarios that cannot be implemented using standard LWC rendering.",
                )
            )
    return findings