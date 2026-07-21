import re
from src.review_core.models import Finding, Severity
from .patterns import LOOP_OPEN
# Detects SOQL queries ([SELECT ...] or Database.query) inside for/while/do loops.
# Apex governor limit: max 100 SOQL queries per transaction — one per loop iteration burns them fast.

_SOQL = re.compile(r"\[?\s*SELECT\b|\bDatabase\.query\s*\(", re.IGNORECASE)


def check_soql_in_loop(code: str) -> list[Finding]:
    """Return findings for every SOQL query detected inside a loop block."""
    findings: list[Finding] = []
    lines = code.splitlines()

    # Track brace depth to identify loop body boundaries
    in_loop_depth: list[int] = []  # stack: brace depth when loop opened
    brace_depth = 0

    for lineno, line in enumerate(lines, start=1):
        # Count braces before checking so we handle same-line opens
        open_braces = line.count("{")
        close_braces = line.count("}")

        # Check if this line opens a loop
        if LOOP_OPEN.search(line):
            in_loop_depth.append(brace_depth + open_braces)

        brace_depth += open_braces - close_braces

        # Pop loop depths that have closed
        in_loop_depth = [d for d in in_loop_depth if brace_depth >= d]

        if in_loop_depth and _SOQL.search(line):
            findings.append(
                Finding(
                    rule="soql_in_loop",
                    severity=Severity.HIGH,
                    line=lineno,
                    message="SOQL query inside loop — risks hitting 100-query governor limit.",
                    suggestion="Collect IDs first, then query once outside the loop using an IN clause.",
                )
            )

    return findings
