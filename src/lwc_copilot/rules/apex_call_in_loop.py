import re
from src.review_core.models import Finding, RuleId, Severity
from src.review_core.patterns import LOOP_OPEN

_APEX_IMPORT = re.compile(r"^\s*import\s+(\w+)\s+from\s+['\"]@salesforce/apex/", re.MULTILINE)


def check_apex_call_in_loop(js_code, html_code):
    brace_depth = 0
    in_loop_depth = []

    apex_names = set(_APEX_IMPORT.findall(js_code))   # {'getContacts'}
    if not apex_names:
        return []
    findings = []
    lines = js_code.splitlines()
    for lineno, line in enumerate(lines, start=1):
        # is one of the imported apex names called on this line?
        called = next((n for n in apex_names if re.search(rf"\b{re.escape(n)}\s*\(", line)), None)

        open_braces = line.count("{")
        close_braces = line.count("}")

        if LOOP_OPEN.search(line):
            in_loop_depth.append(brace_depth + open_braces)

        brace_depth += open_braces - close_braces
        in_loop_depth = [d for d in in_loop_depth if brace_depth >= d]

        if in_loop_depth and called:
            findings.append(
                Finding(
                    rule=RuleId.apex_call_in_loop.value,          # <- fill: which RuleId member?
                    severity=Severity.HIGH,      # <- fill: Severity.HIGH
                    line=lineno,
                    message="Apex call in loop detected.",
                    suggestion="Write proper SOQL Code, instead of calling the database multiple times in loop"
                )
            )
    return findings