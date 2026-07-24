import re
from src.review_core.models import Finding, Severity

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
# Class-level sharing declaration — the ONLY construct that satisfies the class
# sharing requirement. `with sharing` / `without sharing` / `inherited sharing`.
# USER_MODE / SYSTEM_MODE are operational (query/DML) modes, NOT class declarations.
_CLASS_SHARING = re.compile(r"\b(with|without|inherited)\s+sharing\b", re.IGNORECASE)
# System mode (inline query/DML) explicitly bypasses security — operational only.
_SYSTEM_MODE = re.compile(
    r"WITH\s+SYSTEM_MODE|AccessLevel\.SYSTEM_MODE|\bas\s+system\b",
    re.IGNORECASE,
)
# Inline statement-level enforcement (API v56+). These enforce CRUD/FLS on the query/DML itself.
# WITH USER_MODE / AccessLevel.USER_MODE / `as user` also enforce sharing; WITH SECURITY_ENFORCED does NOT.
_INLINE_CRUD_ENFORCED = re.compile(
    r"WITH\s+USER_MODE|WITH\s+SECURITY_ENFORCED|AccessLevel\.USER_MODE|\bas\s+user\b",
    re.IGNORECASE,
)


def check_missing_crud_fls(code: str) -> list[Finding]:
    """Return a finding if DML/SOQL exists but no CRUD/FLS check is present in the file."""
    # TODO (Phase 2): upgrade to method-scoped analysis so checks in one method
    #   don't suppress findings in another method that has no check.

    has_dml_or_soql = bool(_DML_OPS.search(code))
    has_crud_check = bool(_CRUD_CHECK.search(code)) or bool(_INLINE_CRUD_ENFORCED.search(code))
    has_class_sharing = bool(_CLASS_SHARING.search(code))
    has_system_mode = bool(_SYSTEM_MODE.search(code))

    findings: list[Finding] = []

    # Inline enforcement (WITH USER_MODE / SECURITY_ENFORCED / as user) handles CRUD+FLS.
    # System mode is a deliberate bypass — surfaced as explicit_system_mode, not negligence.
    if has_dml_or_soql and not has_crud_check and not has_system_mode:
        findings.append(
            Finding(
                rule="missing_crud_fls",
                severity=Severity.HIGH,
                line=1,
                message="DML or SOQL found with no CRUD/FLS enforcement.",
                suggestion=(
                    "Enforce at the operation: WITH USER_MODE (SOQL) or `as user` (DML), "
                    "or add Schema.sObjectType.MyObject__c.isAccessible() before queries "
                    "and isCreateable()/isUpdateable() before DML."
                ),
            )
        )

    # No class-level sharing keyword → runs as inherited sharing. Not a bug, but best
    # practice is to declare intent explicitly. INFO, not a hard finding.
    if has_dml_or_soql and not has_class_sharing:
        findings.append(
            Finding(
                rule="missing_sharing_declaration",
                severity=Severity.INFO,
                line=1,
                message="No explicit class sharing declaration — runs as inherited sharing.",
                suggestion=(
                    "Good practice: declare 'with sharing', 'without sharing', or "
                    "'inherited sharing' on the class to make the sharing intent explicit."
                ),
            )
        )

    if has_system_mode:
        findings.append(
            Finding(
                rule="explicit_system_mode",
                severity=Severity.INFO,
                line=1,
                message="Operation uses system mode — bypasses sharing, CRUD, and FLS.",
                suggestion="Confirm this is intentional. Document why system-level access is required.",
            )
        )

    return findings
