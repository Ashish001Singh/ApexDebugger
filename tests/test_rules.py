import pytest
from src.apex_copilot.rules.soql_in_loop import check_soql_in_loop
from src.apex_copilot.rules.dml_in_loop import check_dml_in_loop
from src.apex_copilot.rules.hardcoded_id import check_hardcoded_id
from src.apex_copilot.rules.missing_crud_fls import check_missing_crud_fls
from src.apex_copilot.reasoning.models import Severity


# ── soql_in_loop ─────────────────────────────────────────────────────────────

SOQL_IN_LOOP = """\
public class Bad {
    public void run(List<Id> ids) {
        for (Id i : ids) {
            List<Account> accs = [SELECT Id FROM Account WHERE Id = :i];
        }
    }
}"""

SOQL_OUTSIDE_LOOP = """\
public class Good {
    public void run(List<Id> ids) {
        List<Account> accs = [SELECT Id FROM Account WHERE Id IN :ids];
    }
}"""


def test_soql_in_loop_detects():
    findings = check_soql_in_loop(SOQL_IN_LOOP)
    assert len(findings) == 1
    assert findings[0].rule == "soql_in_loop"
    assert findings[0].severity == Severity.HIGH


def test_soql_outside_loop_clean():
    findings = check_soql_in_loop(SOQL_OUTSIDE_LOOP)
    assert findings == []


# ── dml_in_loop ──────────────────────────────────────────────────────────────

DML_IN_LOOP = """\
public class Bad {
    public void run(List<Account> accs) {
        for (Account a : accs) {
            a.Name = 'Updated';
            update a;
        }
    }
}"""

DML_OUTSIDE_LOOP = """\
public class Good {
    public void run(List<Account> accs) {
        for (Account a : accs) {
            a.Name = 'Updated';
        }
        update accs;
    }
}"""


def test_dml_in_loop_detects():
    findings = check_dml_in_loop(DML_IN_LOOP)
    assert len(findings) == 1
    assert findings[0].rule == "dml_in_loop"
    assert findings[0].severity == Severity.HIGH


def test_dml_outside_loop_clean():
    findings = check_dml_in_loop(DML_OUTSIDE_LOOP)
    assert findings == []


# ── hardcoded_id ─────────────────────────────────────────────────────────────

HARDCODED_SF_ID = """\
public class Bad {
    private static final Id RT_ID = '012000000000AAAAAQ';
}"""

HARDCODED_ID_VIA_CONTEXT = """\
public class Bad {
    public void run() {
        acc.OwnerId = 'XXXXXXXXXXXXXXXXX1';
    }
}"""

HARDCODED_EXTERNAL_ID_FIELD = """\
public class Bad {
    public void run() {
        account.ExternalCustomerId__c = 'SAP-CUST-2024-001';
    }
}"""

NO_HARDCODED_ID = """\
public class Good {
    private static final String NAME = 'Hello World';
}"""


def test_hardcoded_sf_id_detects():
    findings = check_hardcoded_id(HARDCODED_SF_ID)
    assert any(f.rule == "hardcoded_id" for f in findings)
    assert findings[0].severity.value == "high"


def test_hardcoded_id_via_context_detects():
    findings = check_hardcoded_id(HARDCODED_ID_VIA_CONTEXT)
    assert any(f.rule == "hardcoded_id" for f in findings)


def test_hardcoded_external_id_field_detects():
    findings = check_hardcoded_id(HARDCODED_EXTERNAL_ID_FIELD)
    assert any(f.rule == "hardcoded_external_id" for f in findings)


def test_no_hardcoded_id_clean():
    findings = check_hardcoded_id(NO_HARDCODED_ID)
    assert findings == []


# ── missing_crud_fls ─────────────────────────────────────────────────────────

MISSING_CRUD = """\
public class Bad {
    public void run() {
        List<Account> accs = [SELECT Id FROM Account];
        insert accs;
    }
}"""

HAS_CRUD_LEGACY = """\
public with sharing class Good {
    public void run() {
        if (Schema.sObjectType.Account.isAccessible()) {
            List<Account> accs = [SELECT Id FROM Account];
        }
    }
}"""

# Inline WITH USER_MODE enforces CRUD/FLS; class-level 'with sharing' covers sharing.
HAS_USER_MODE = """\
public with sharing class Best {
    public void run() {
        List<Account> accs = [SELECT Id FROM Account WITH USER_MODE];
    }
}"""

# Inline WITH SYSTEM_MODE = deliberate bypass → explicit_system_mode (INFO).
WITH_SYSTEM_MODE = """\
public with sharing class SystemClass {
    public void run() {
        List<Account> accs = [SELECT Id FROM Account WITH SYSTEM_MODE];
    }
}"""


def test_missing_crud_detects():
    findings = check_missing_crud_fls(MISSING_CRUD)
    rules = [f.rule for f in findings]
    assert "missing_crud_fls" in rules


def test_legacy_with_sharing_and_crud_check_no_finding():
    findings = check_missing_crud_fls(HAS_CRUD_LEGACY)
    rules = [f.rule for f in findings]
    assert "missing_crud_fls" not in rules


def test_user_mode_suppresses_crud_finding():
    findings = check_missing_crud_fls(HAS_USER_MODE)
    rules = [f.rule for f in findings]
    assert "missing_crud_fls" not in rules
    assert "missing_sharing_declaration" not in rules


def test_system_mode_flags_info():
    findings = check_missing_crud_fls(WITH_SYSTEM_MODE)
    rules = [f.rule for f in findings]
    assert "explicit_system_mode" in rules
