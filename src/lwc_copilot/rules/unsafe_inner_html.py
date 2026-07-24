import re
from src.review_core.models import Finding, RuleId, Severity

_INNER_HTML_ASSIGN = re.compile(r"\.innerHTML\s*=(?!=)")

def check_unsafe_inner_html(js_code: str, html_code: str) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(js_code.splitlines(), start=1):
        if _INNER_HTML_ASSIGN.search(line):
            findings.append(
                Finding(
                    rule=RuleId.unsafe_inner_html.value,          # <- fill: which RuleId member?
                    severity=Severity.HIGH,      # <- fill: Severity.HIGH
                    line=lineno,
                    message="Direct innerHTML assignment bypasses LWC's built-in XSS protection.",
                    suggestion="Use textContent for text, or lightning-formatted-rich-text for sanitized HTML.",
                )
            )
    return findings