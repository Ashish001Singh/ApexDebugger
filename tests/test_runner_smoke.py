from src.apex_copilot.review import review
from src.apex_copilot.reasoning.models import ReviewResult
import pytest 

pytestmark = pytest.mark.integration

def test_review_returns_result():
    code = "public class Empty {}"
    result = review(code, filename="Empty.cls")
    assert isinstance(result, ReviewResult)
    assert result.filename == "Empty.cls"
    assert isinstance(result.findings, list)


def test_review_detects_soql_in_loop():
    code = """\
public class Test {
    public void run(List<Id> ids) {
        for (Id i : ids) {
            List<Account> a = [SELECT Id FROM Account WHERE Id = :i];
        }
    }
}"""
    result = review(code)
    rules = [f.rule for f in result.findings]
    assert "soql_in_loop" in rules
