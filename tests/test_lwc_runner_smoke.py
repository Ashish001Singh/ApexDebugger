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
