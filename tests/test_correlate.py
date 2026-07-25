from pathlib import Path
from src.orchestrator.correlate import correlate
from src.orchestrator.run import resolve_controller_findings
from src.orchestrator.route import LwcBundle
from src.review_core.models import ReviewResult, Finding, Severity
from src.orchestrator.run import resolve_controller_findings, _build_pairs


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


# ── resolve_controller_findings: pull in unchanged controllers, regex-only ──

INSECURE_CONTROLLER = """\
public class AccountController {
    @AuraEnabled(cacheable=true)
    public static List<Account> getAccounts() {
        return [SELECT Id, Name FROM Account];
    }
}"""


def test_resolves_unchanged_controller_from_repo(tmp_path):
    # An LWC imports AccountController, but the .cls is NOT in the reviewed set.
    classes = tmp_path / "classes"
    classes.mkdir()
    (classes / "AccountController.cls").write_text(INSECURE_CONTROLLER)

    bundle_dir = tmp_path / "lwc" / "accountList"
    bundle_dir.mkdir(parents=True)
    js = bundle_dir / "accountList.js"
    js.write_text(LWC_CALLING_ACCOUNTCONTROLLER)
    bundle = LwcBundle(js=js, html=None)

    extra = resolve_controller_findings([bundle], existing_results=[], repo_root=tmp_path)

    assert len(extra) == 1
    assert Path(extra[0].filename).stem == "AccountController"
    rules = {f.rule.value for f in extra[0].findings}
    assert "missing_crud_fls" in rules   # regex found the security gap, free


def test_skips_controller_already_reviewed(tmp_path):
    classes = tmp_path / "classes"
    classes.mkdir()
    (classes / "AccountController.cls").write_text(INSECURE_CONTROLLER)
    bundle_dir = tmp_path / "lwc" / "accountList"
    bundle_dir.mkdir(parents=True)
    js = bundle_dir / "accountList.js"
    js.write_text(LWC_CALLING_ACCOUNTCONTROLLER)
    bundle = LwcBundle(js=js, html=None)

    already = [ReviewResult(filename="AccountController.cls", findings=[])]
    extra = resolve_controller_findings([bundle], existing_results=already, repo_root=tmp_path)

    assert extra == []   # already in the reviewed set → don't re-scan

def test_build_pairs_matches_lwc_to_controller_source(tmp_path):
    js = tmp_path / "leadList.js"
    js.write_text(LWC_CALLING_ACCOUNTCONTROLLER)   # imports AccountController
    bundle = LwcBundle(js=js, html=None)
    apex_sources = {"AccountController": ("AccountController.cls", INSECURE_CONTROLLER)}

    pairs = _build_pairs([bundle], apex_sources)

    assert len(pairs) == 1
    assert pairs[0].apex_code == INSECURE_CONTROLLER
    assert pairs[0].lwc_file == str(js)