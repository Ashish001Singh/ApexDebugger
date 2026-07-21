from src.lwc_copilot.rules.unsafe_inner_html import check_unsafe_inner_html
from src.review_core.models import Severity

UNSAFE_INNER_HTML = """\
export default class Bad extends LightningElement {
    renderedCallback() {
        this.template.querySelector('div').innerHTML = this.rawUserInput;
    }
}"""

SAFE_TEXT_CONTENT = """\
export default class Good extends LightningElement {
    renderedCallback() {
        this.template.querySelector('div').textContent = this.rawUserInput;
    }
}"""


def test_inner_html_assignment_detects():
    findings = check_unsafe_inner_html(UNSAFE_INNER_HTML, "")
    assert len(findings) == 1
    assert findings[0].rule == "unsafe_inner_html"
    assert findings[0].severity == Severity.HIGH


def test_text_content_clean():
    findings = check_unsafe_inner_html(SAFE_TEXT_CONTENT, "")
    assert findings == []
