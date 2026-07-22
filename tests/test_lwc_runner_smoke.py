import pytest
from src.lwc_copilot.reasoning.graph import run_reasoning_graph
from src.review_core.models import ReviewResult

pytestmark = pytest.mark.integration


def test_lwc_reasoning_returns_result():
    js = "export default class Empty extends LightningElement {}"
    result = run_reasoning_graph(js, "<template></template>", [], filename="empty.js")
    assert isinstance(result, ReviewResult)
    assert result.filename == "empty.js"
    assert isinstance(result.findings, list)


from src.lwc_copilot.review import review as lwc_review


def test_lwc_review_detects_unsafe_inner_html():
    js = """\
export default class Bad extends LightningElement {
    renderedCallback() {
        this.template.querySelector('div').innerHTML = this.raw;
    }
}"""
    result = lwc_review(js, "", filename="bad.js")
    rules = [f.rule for f in result.findings]
    assert "unsafe_inner_html" in rules
