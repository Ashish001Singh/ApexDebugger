import re
from src.apex_copilot.reasoning.models import Finding, Severity

# CRUD/FLS: code must check object-level (isAccessible/isCreateable/isUpdateable/isDeletable)
# and field-level (getDescribe().isAccessible()) permissions before DML or SOQL.
# Missing checks = security vulnerability (PMD ApexCRUDViolation, OWASP A01).
#
# Access control modes (API v56+ / Summer '22):
#   with user mode   → enforces sharing + CRUD + FLS automatically (preferred)
#   with system mode → explicitly bypasses all (document why if used)
#   with sharing     → enforces sharing only; CRUD/FLS still need manual checks
#   without sharing  → bypasses sharing; CRUD/FLS still need manual checks

_DML_OPS = re.compile(
    r"\b(insert|update|delete|upsert|merge|undelete)\b\s+\w|\[?\s*SELECT\b",
    re.IGNORECASE,
)
_CRUD_CHECK = re.compile(
    r"\.(isAccessible|isCreateable|isUpdateable|isDeletable|isReadable)\s*\(\)",
    re.IGNORECASE,
)
# with user mode = full enforcement (CRUD+FLS+sharing). with sharing = sharing only.
_USER_MODE = re.compile(r"\bwith\s+user\s+mode\b", re.IGNORECASE)
_WITH_SHARING = re.compile(r"\bwith\s+sharing\b", re.IGNORECASE)
_SYSTEM_MODE = re.compile(r"\bwith\s+system\s+mode\b", re.IGNORECASE)


def check_missing_crud_fls(code: str) -> list[Finding]:
    """Return a finding if DML/SOQL exists but no CRUD/FLS check is present in the file."""
    # TODO (Phase 2): upgrade to method-scoped analysis so checks in one method
    #   don't suppress findings in another method that has no check.

    has_dml_or_soql = bool(_DML_OPS.search(code))
    has_crud_check = bool(_CRUD_CHECK.search(code))
    has_user_mode = bool(_USER_MODE.search(code))
    has_with_sharing = bool(_WITH_SHARING.search(code))
    has_system_mode = bool(_SYSTEM_MODE.search(code))

    findings: list[Finding] = []

    # with user mode enforces CRUD+FLS automatically — no manual checks needed
    if has_dml_or_soql and not has_user_mode and not has_crud_check:
        findings.append(
            Finding(
                rule="missing_crud_fls",
                severity=Severity.HIGH,
                line=1,
                message="DML or SOQL found with no CRUD/FLS enforcement.",
                suggestion=(
                    "Preferred (API v56+): declare class 'with user mode' — enforces sharing, "
                    "CRUD, and FLS automatically. "
                    "Legacy: add Schema.sObjectType.MyObject__c.isAccessible() before queries "
                    "and isCreateable()/isUpdateable() before DML."
                ),
            )
        )

    # Flag if no access-control keyword at all
    if has_dml_or_soql and not has_user_mode and not has_with_sharing and not has_system_mode:
        findings.append(
            Finding(
                rule="missing_sharing_declaration",
                severity=Severity.MEDIUM,
                line=1,
                message="Class performs DML/SOQL but has no sharing/access-mode declaration.",
                suggestion=(
                    "Add 'with user mode' (API v56+, enforces sharing + CRUD + FLS) "
                    "or 'with sharing' (enforces sharing only) to the class declaration."
                ),
            )
        )

    if has_system_mode:
        findings.append(
            Finding(
                rule="explicit_system_mode",
                severity=Severity.INFO,
                line=1,
                message="Class uses 'with system mode' — bypasses all sharing, CRUD, and FLS.",
                suggestion="Confirm this is intentional. Document why system-level access is required.",
            )
        )

    return findings
