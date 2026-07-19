import re
from src.apex_copilot.reasoning.models import Finding, Severity

# Hardcoded ID detection — two categories:
#
# 1. Salesforce record IDs (15 or 18 char, known entity key prefix)
#    Problem: IDs are org-specific. sandbox ID != production ID. Breaks deploys.
#
# 2. External IDs (arbitrary strings in external-ID field assignments or upsert contexts)
#    Problem: external system keys change per environment (dev/staging/prod).
#    No structural way to detect these — Phase 2 uses LLM context window for this.

# ── Salesforce entity key prefixes (first 3 chars of every SF record ID) ─────
_KNOWN_PREFIXES = {
    "001",  # Account
    "003",  # Contact
    "005",  # User
    "006",  # Opportunity
    "007",  # Activity
    "00D",  # Organization
    "00E",  # Profile
    "00G",  # Group
    "00N",  # Custom field
    "00O",  # Report
    "00P",  # Attachment
    "00Q",  # Lead
    "00T",  # Task
    "00U",  # Event
    "012",  # RecordType
    "013",  # PersonAccount
    "014",  # Document
    "015",  # ContentVersion
    "017",  # ContentDocument
}

# ── Patterns ──────────────────────────────────────────────────────────────────

_STRING_LITERAL = re.compile(r"'([^']{10,25})'")  # only 10-25 char strings (ID range)

# Variable declared as Id type: `Id someVar = '...'` or `Id someVar='...'`
_ID_TYPE_DECL = re.compile(r"\bId\s+\w+\s*=", re.IGNORECASE)

# Field or variable name that strongly suggests an SF record ID
_ID_FIELD_NAME = re.compile(
    r"\b\w*(RecordTypeId|OwnerId|AccountId|ContactId|ParentId|CreatedById"
    r"|LastModifiedById|MasterRecordId|[A-Za-z]+Id)\b\s*=",
)

# Database.upsert(record, SomeObject.ExternalField__c) — second arg is field token, not string
# We flag string literals passed to methods known to use external IDs
_UPSERT_WITH_LITERAL = re.compile(
    r"\bDatabase\.upsert\s*\([^,]+,\s*['\"]",
    re.IGNORECASE,
)

# External ID field assignment: obj.SomeName__c = 'literal'
# __c suffix = custom field; if name contains External or ExtId → likely external ID
_EXTERNAL_ID_FIELD = re.compile(
    r"\b\w+\.([\w]*[Ee]xternal[\w]*|[\w]*[Ee]xt[_]?[Ii]d[\w]*)__c\s*=\s*'",
    re.IGNORECASE,
)


def _is_sf_record_id(s: str) -> bool:
    if len(s) not in (15, 18):
        return False
    if not s.isalnum():
        return False
    return s[:3] in _KNOWN_PREFIXES


def _line_suggests_id_context(line: str) -> bool:
    """True if same line has strong signals this string is being used as an SF ID."""
    return bool(_ID_TYPE_DECL.search(line) or _ID_FIELD_NAME.search(line))


def check_hardcoded_id(code: str) -> list[Finding]:
    """
    Detect hardcoded Salesforce record IDs and external IDs.

    Phase 1: structural checks — known key prefixes + same-line context signals.
    Phase 2 TODO: for strings without known prefix, send 5-line window to Claude
                  and ask "is this a hardcoded SF or external ID?"
    """
    findings: list[Finding] = []
    lines = code.splitlines()

    for lineno, line in enumerate(lines, start=1):
        # ── Check 1: known SF record ID prefix ───────────────────────────────
        for match in _STRING_LITERAL.finditer(line):
            candidate = match.group(1)
            if _is_sf_record_id(candidate):
                findings.append(
                    Finding(
                        rule="hardcoded_id",
                        severity=Severity.HIGH,
                        line=lineno,
                        message=f"Hardcoded Salesforce record ID '{candidate}' — org-specific, breaks cross-org deploys.",
                        suggestion="Store in Custom Metadata Type or Custom Setting and query by DeveloperName.",
                    )
                )
                continue  # don't double-flag same string

            # ── Check 2: no known prefix, but context strongly suggests ID ───
            # e.g. `Id ownerId = 'SomeLiteralHere';`
            if _line_suggests_id_context(line) and len(candidate) in (15, 18) and candidate.isalnum():
                findings.append(
                    Finding(
                        rule="hardcoded_id",
                        severity=Severity.MEDIUM,
                        line=lineno,
                        message=f"String '{candidate}' assigned to an Id-typed variable/field — likely a hardcoded record ID.",
                        suggestion="Store in Custom Metadata Type or Custom Setting and query by DeveloperName.",
                    )
                )

        # ── Check 3: external ID field assignment ─────────────────────────────
        if _EXTERNAL_ID_FIELD.search(line):
            findings.append(
                Finding(
                    rule="hardcoded_external_id",
                    severity=Severity.MEDIUM,
                    line=lineno,
                    message="Literal value assigned to an external ID field — environment-specific, breaks deploys.",
                    suggestion="Pass external ID values as parameters or load from Custom Metadata / environment config.",
                )
            )

        # ── Check 4: Database.upsert with string literal as second arg ────────
        if _UPSERT_WITH_LITERAL.search(line):
            findings.append(
                Finding(
                    rule="hardcoded_external_id",
                    severity=Severity.MEDIUM,
                    line=lineno,
                    message="Database.upsert called with a string literal as external ID field reference.",
                    suggestion="Use a Schema.SObjectField token (e.g. Account.MyField__c) not a string literal.",
                )
            )

    return findings
