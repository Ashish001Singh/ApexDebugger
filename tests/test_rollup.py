import pytest
from src.orchestrator.rollup import rollup
from src.review_core.models import ReviewResult, Finding, Severity


def _f(rule, line):
    return Finding(rule=rule, severity=Severity.HIGH, line=line, message="x", suggestion="y")


def test_rollup_gated_below_threshold_makes_no_call():
    results = [ReviewResult(filename="A.cls", findings=[_f("soql_in_loop", 1), _f("dml_in_loop", 2)])]
    assert rollup(results) is None     # 2 findings < 3 → ?


@pytest.mark.integration
def test_rollup_summarizes_when_over_threshold():
    findings = [
        _f("soql_in_loop", 4), _f("dml_in_loop", 6), _f("hardcoded_id", 9),
    ]
    results = [ReviewResult(filename="Messy.cls", findings=findings)]
    summary = rollup(results)

    assert summary is not None
    assert len(summary.strip()) > 20