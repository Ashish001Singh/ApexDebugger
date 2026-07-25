from src.orchestrator.correlate import correlate
from src.review_core.models import ReviewResult, Finding, Severity


def _finding(rule):
    return Finding(rule=rule, severity=Severity.HIGH, line=1, message="x", suggestion="y")


LWC_CALLING_ACCOUNTCONTROLLER = """\
import getAccounts from '@salesforce/apex/AccountController.getAccounts';

export default class AccountList extends LightningElement {
    @wire(getAccounts)
    accounts;
}"""


def test_lwc_calling_insecure_apex_flags_cross_language_risk():
    results = [
        ReviewResult(filename="AccountController.cls", findings=[_finding("missing_crud_fls")]),
        ReviewResult(filename="accountList.js", findings=[]),
    ]
    lwc_sources = {"accountList.js": LWC_CALLING_ACCOUNTCONTROLLER}

    findings = correlate(results, lwc_sources)

    assert len(findings) == 1
    assert findings[0].rule == "cross_language_security_risk"


def test_lwc_calling_secure_apex_no_flag():
    results = [
        ReviewResult(filename="AccountController.cls", findings=[]),  # no security gap
        ReviewResult(filename="accountList.js", findings=[]),
    ]
    lwc_sources = {"accountList.js": LWC_CALLING_ACCOUNTCONTROLLER}

    findings = correlate(results, lwc_sources)

    assert findings == []


def test_lwc_calling_unreviewed_controller_no_flag():
    # The imported controller wasn't reviewed → nothing to correlate against.
    results = [
        ReviewResult(filename="accountList.js", findings=[]),
    ]
    lwc_sources = {"accountList.js": LWC_CALLING_ACCOUNTCONTROLLER}

    findings = correlate(results, lwc_sources)

    assert findings == []
