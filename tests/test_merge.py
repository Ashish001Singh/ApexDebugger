from src.apex_copilot.reasoning.models import Finding
from src.apex_copilot.reasoning.graph import merge_findings
from src.apex_copilot.reasoning.models import Severity



def test_no_overlap():
    finding_llm = [Finding(rule="soql_in_loop", severity=Severity.HIGH, line=4, message="x", suggestion="y")]
    finding_regex = [Finding(rule="dml_in_loop", severity=Severity.HIGH, line=10, message="x", suggestion="y")]
    merged_findings = merge_findings(finding_regex,finding_llm)
    assert len(merged_findings) == 2



def test_exact_overlap():
    finding_llm = [Finding(rule="soql_in_loop", severity=Severity.HIGH, line=4, message="x", suggestion="y")]
    finding_regex = [Finding(rule="soql_in_loop", severity=Severity.HIGH, line=4, message="x", suggestion="y")]
    merged_findings = merge_findings(finding_regex,finding_llm)
    assert len(merged_findings) == 1

def test_same_rule_overlap():
    finding_llm = [Finding(rule="soql_in_loop", severity=Severity.HIGH, line=4, message="x", suggestion="y")]
    finding_regex = [Finding(rule="soql_in_loop", severity=Severity.HIGH, line=10, message="x", suggestion="y")]
    merged_findings = merge_findings(finding_regex,finding_llm)
    assert len(merged_findings) == 2


def test_no_llm_finding_rule_overlap():
    finding_llm = []
    finding_regex = [Finding(rule="soql_in_loop", severity=Severity.HIGH, line=4, message="x", suggestion="y")]
    merged_findings = merge_findings(finding_regex,finding_llm)
    assert len(merged_findings) == 1
    assert merged_findings[0].rule == "soql_in_loop"