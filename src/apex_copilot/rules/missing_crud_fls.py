import re
from src.apex_copilot.reasoning.models import Finding, Severity

# CRUD/FLS: code must check object-level (isAccessible/isCreateable/isUpdateable/isDeletable)
# and field-level (getDescribe().isAccessible()) permissions before DML or SOQL.
# Missing checks = security vulnerability (PMD ApexCRUDViolation, OWASP A01).

_DML_OPS = re.compile(
    r"\b(insert|update|delete|upsert|merge|undelete)\b\s+\w|\[?\s*SELECT\b",
    re.IGNORECASE,
)
_CRUD_CHECK = re.compile(
    r"\.(isAccessible|isCreateable|isUpdateable|isDeletable|isReadable)\s*\(\)",
    re.IGNORECASE,
)
_WITH_SHARING = re.compile(r"\bwith\s+sharing\b", re.IGNORECASE)


def check_missing_crud_fls(code: str) -> list[Finding]:
    """Return a finding if DML/SOQL exists but no CRUD/FLS check is present in the file."""
    # TODO (Phase 2): upgrade to method-scoped analysis so checks in one method
    #   don't suppress findings in another method that has no check.

    has_dml_or_soql = bool(_DML_OPS.search(code))
    has_crud_check = bool(_CRUD_CHECK.search(code))
    has_with_sharing = bool(_WITH_SHARING.search(code))

    findings: list[Finding] = []

    if has_dml_or_soql and not has_crud_check:
        findings.append(
            Finding(
                rule="missing_crud_fls",
                severity=Severity.HIGH,
                line=1,
                message="DML or SOQL found with no CRUD/FLS permission check in this file.",
                suggestion=(
                    "Add Schema.sObjectType.MyObject__c.isAccessible() checks before queries "
                    "and isCreateable()/isUpdateable() before DML. "
                    "Also declare 'with sharing' on the class."
                ),
            )
        )

    if has_dml_or_soql and not has_with_sharing:
        findings.append(
            Finding(
                rule="missing_with_sharing",
                severity=Severity.MEDIUM,
                line=1,
                message="Class performs DML/SOQL but is not declared 'with sharing'.",
                suggestion="Add 'with sharing' to the class declaration to enforce record-level security.",
            )
        )

    return findings
