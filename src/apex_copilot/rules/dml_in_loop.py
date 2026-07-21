import re
from src.review_core.models import Finding, Severity
from src.review_core.patterns import LOOP_OPEN

# Detects DML statements (insert/update/delete/upsert/merge/undelete) inside loops.
# Apex governor limit: max 150 DML statements per transaction.

_DML = re.compile(
    r"\b(insert|update|delete|upsert|merge|undelete)\b\s+\w",
    re.IGNORECASE,
)


def check_dml_in_loop(code: str) -> list[Finding]:
    """Return findings for every DML statement detected inside a loop block."""
    findings: list[Finding] = []
    lines = code.splitlines()

    in_loop_depth: list[int] = []
    brace_depth = 0

    for lineno, line in enumerate(lines, start=1):
        open_braces = line.count("{")
        close_braces = line.count("}")

        if LOOP_OPEN.search(line):
            in_loop_depth.append(brace_depth + open_braces)

        brace_depth += open_braces - close_braces
        in_loop_depth = [d for d in in_loop_depth if brace_depth >= d]

        if in_loop_depth and _DML.search(line):
            findings.append(
                Finding(
                    rule="dml_in_loop",
                    severity=Severity.HIGH,
                    line=lineno,
                    message="DML statement inside loop — risks hitting 150-DML governor limit.",
                    suggestion="Collect records in a List, then perform a single DML call outside the loop.",
                )
            )

    return findings
