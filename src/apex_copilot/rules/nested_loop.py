
from src.apex_copilot.reasoning.models import Finding, Severity,RuleId
import re

_LOOP_OPEN = re.compile(r"\b(for|while|do)\b[^{;]*\{", re.IGNORECASE | re.DOTALL)

def check_nested_loop(code: str) -> list[Finding]:
    findings = []
    in_loop_depth = []
    brace_depth = 0
    for lineno, line in enumerate(code.splitlines(), start=1):
        open_braces = line.count("{")
        close_braces = line.count("}")

        if _LOOP_OPEN.search(line):
            in_loop_depth.append(brace_depth + open_braces)
            depth = len(in_loop_depth)          # ← current nesting level
            if depth == 2:
                findings.append(Finding(
                rule=RuleId.nested_loop_2,
                severity=Severity.MEDIUM,
                line=lineno,
                message="Nested Loop of Level 2 is found",
                suggestion=(
                    "Nested Loop of Level 2 is found. Check if we can rectify this"
                ),
            ))
            if depth==3:
                 findings.append(Finding(
                rule=RuleId.nested_loop_deep,
                severity=Severity.HIGH,
                line=lineno,
                message="More then three level of Nested Level found risky",
                suggestion=(
                    "Nested Loop of Level 3 is found. Please fix this. This can lead to cpu/heap risk "
                ),
            ))

        brace_depth += open_braces - close_braces
        in_loop_depth = [d for d in in_loop_depth if brace_depth >= d]

    return findings