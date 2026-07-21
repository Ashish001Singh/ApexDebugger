import re
from src.review_core.models import Finding, RuleId, Severity

_APEX_IMPORT = re.compile(r"^\s*import\s+(\w+)\s+from\s+['\"]@salesforce/apex/", re.MULTILINE)

def check_imperative_apex_no_error_handling(js_code, html_code):
    apex_names = set(_APEX_IMPORT.findall(js_code))   # {'getContacts'}
    if not apex_names:
        return []
    findings = []
    lines = js_code.splitlines()
    for lineno, line in enumerate(lines, start=1):
        # is one of the imported apex names called on this line?
        called = next((n for n in apex_names if re.search(rf"\b{re.escape(n)}\s*\(", line)), None)
        if called is None:
            continue
        window = "\n".join(lines[lineno-1 : lineno-1+8])   # 8-line lookahead
        if ".then(" in window and ".catch(" not in window:
            findings.append(
                Finding(
                    rule=RuleId.imperative_apex_no_error_handling.value,          # <- fill: which RuleId member?
                    severity=Severity.MEDIUM,      # <- fill: Severity.HIGH
                    line=lineno,
                    message="Imperative Apex call detected without error handling.",
                    suggestion="Wrap the imperative Apex call in try/catch when using "
                        "async/await, or add a '.catch()' handler when using Promises "
                        "to handle exceptions gracefully.",
                )
            )
    return findings