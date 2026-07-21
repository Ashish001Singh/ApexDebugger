
# NOTE: line-based — assumes one loop-open per line (standard Apex formatting).
# Multiple loops on a single line are undercounted. Same limitation as soql_in_loop.

from src.review_core.models import Finding, Severity,RuleId
import re
from src.review_core.patterns import LOOP_OPEN


def check_nested_loop(code: str) -> list[Finding]:
    findings = []
    in_loop_depth = []
    brace_depth = 0
    for lineno, line in enumerate(code.splitlines(), start=1):
        open_braces = line.count("{")
        close_braces = line.count("}")

        if LOOP_OPEN.search(line):
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