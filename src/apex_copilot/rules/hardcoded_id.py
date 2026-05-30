import re
from src.apex_copilot.reasoning.models import Finding, Severity

# Salesforce IDs are 15-char (case-sensitive) or 18-char (case-insensitive) strings
# starting with a known 3-char entity prefix.
# Hardcoded IDs break when code is deployed to a different org (IDs are org-specific).

_SF_ID = re.compile(
    r"""(?<![A-Za-z0-9_'"])   # not preceded by word char or quote (avoid partial matches)
    ([a-zA-Z0-9]{15}|[a-zA-Z0-9]{18})
    (?![A-Za-z0-9_'"])        # not followed by word char or quote
    """,
    re.VERBOSE,
)

# Common Salesforce key prefixes (entity type encoded in first 3 chars)
_KNOWN_PREFIXES = {
    "001", "003", "005", "006", "007", "00D", "00E", "00G", "00N", "00O",
    "00P", "00Q", "00R", "00T", "00U", "012", "013", "014", "015", "017",
}

_STRING_LITERAL = re.compile(r"'([^']*)'")


def _looks_like_sf_id(s: str) -> bool:
    if len(s) not in (15, 18):
        return False
    prefix = s[:3]
    return prefix in _KNOWN_PREFIXES or (prefix[0].isdigit() is False and prefix.isalnum())


def check_hardcoded_id(code: str) -> list[Finding]:
    """Return findings for string literals that look like Salesforce record IDs."""
    findings: list[Finding] = []
    for lineno, line in enumerate(code.splitlines(), start=1):
        for match in _STRING_LITERAL.finditer(line):
            candidate = match.group(1)
            if _looks_like_sf_id(candidate):
                findings.append(
                    Finding(
                        rule="hardcoded_id",
                        severity=Severity.MEDIUM,
                        line=lineno,
                        message=f"Possible hardcoded Salesforce ID '{candidate}' — IDs are org-specific.",
                        suggestion="Store IDs in Custom Metadata, Custom Settings, or pass as parameters.",
                    )
                )
    return findings
