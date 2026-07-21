from src.apex_copilot.reasoning.graph import vote_findings
from src.review_core.models import Finding, Severity

def test_vote_keeps_majority_drops_noise():
    from src.review_core.models import Finding, Severity
    def F(rule): return Finding(rule=rule, severity=Severity.HIGH, line=1, message="x", suggestion="y")
    runs = [
        [F("hardcoded_id"), F("missing_crud_fls")],   # run1
        [F("hardcoded_id"), F("dml_in_loop")],        # run2
        [F("hardcoded_id")],                          # run3
    ]
    kept = {f.rule.value for f in vote_findings(runs, threshold=2)}
    assert kept == {"hardcoded_id"}   # 3/3 kept; noise (1/3 each) dropped