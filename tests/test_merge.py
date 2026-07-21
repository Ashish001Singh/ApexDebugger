from src.review_core.models import Finding
from src.review_core.merging import merge_findings
from src.review_core.models import Severity
from src.apex_copilot.reasoning.graph import REGEX_OWNED


def test_no_overlap():
    finding_llm = [Finding(rule="soql_in_loop", severity=Severity.HIGH, line=4, message="x", suggestion="y")]
    finding_regex = [Finding(rule="dml_in_loop", severity=Severity.HIGH, line=10, message="x", suggestion="y")]
    merged_findings = merge_findings(finding_regex,finding_llm, REGEX_OWNED)
    assert len(merged_findings) == 2

def test_exact_overlap():
    finding_llm = [Finding(rule="soql_in_loop", severity=Severity.HIGH, line=4, message="x", suggestion="y")]
    finding_regex = [Finding(rule="soql_in_loop", severity=Severity.HIGH, line=4, message="x", suggestion="y")]
    merged_findings = merge_findings(finding_regex,finding_llm, REGEX_OWNED)
    assert len(merged_findings) == 1

def test_no_llm_finding_rule_overlap():
    finding_llm = []
    finding_regex = [Finding(rule="soql_in_loop", severity=Severity.HIGH, line=4, message="x", suggestion="y")]
    merged_findings = merge_findings(finding_regex,finding_llm, REGEX_OWNED)
    assert len(merged_findings) == 1
    assert merged_findings[0].rule == "soql_in_loop"

def test_drops_llm_finding_on_regex_owned_rule():
    regex = []   # regex found nothing (e.g. isCreateable present)
    llm = [Finding(rule="missing_crud_fls", severity=Severity.HIGH, line=1, message="x", suggestion="y")]
    kept = {f.rule.value for f in merge_findings(regex, llm, REGEX_OWNED)}
    assert "missing_crud_fls" not in kept       # dropped — regex owns it

def test_keeps_llm_finding_on_llm_owned_rule():
    regex = []
    llm = [Finding(rule="high_complexity", severity=Severity.MEDIUM, line=1, message="x", suggestion="y")]
    kept = {f.rule.value for f in merge_findings(regex, llm, REGEX_OWNED)}
    assert "high_complexity" in kept            # kept — only LLM can find it



def test_llm_regex_owned_rule_dropped_even_at_different_line():
    regex = [Finding(rule="soql_in_loop", severity=Severity.HIGH, line=4, message="x", suggestion="y")]
    llm   = [Finding(rule="soql_in_loop", severity=Severity.HIGH, line=6, message="x", suggestion="y")]
    kept = merge_findings(regex, llm, REGEX_OWNED)
    assert len(kept) == 1            # LLM's regex-owned claim dropped; regex floor stays


def test_no_overlap():
    regex = [Finding(rule="dml_in_loop", severity=Severity.HIGH, line=10, message="x", suggestion="y")]
    llm   = [Finding(rule="high_complexity", severity=Severity.HIGH, line=4, message="x", suggestion="y")]
    merged = merge_findings(regex, llm, REGEX_OWNED)
    assert len(merged) == 2          # regex floor + LLM-owned finding kept