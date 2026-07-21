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


from src.lwc_copilot.rules.manual_dom_manipulation import check_manual_dom_manipulation

MANUAL_DOM_TEMPLATE = """\
<template>
    <div lwc:dom="manual"></div>
</template>"""

STANDARD_TEMPLATE = """\
<template>
    <div>{greeting}</div>
</template>"""


def test_manual_dom_detects():
    findings = check_manual_dom_manipulation("", MANUAL_DOM_TEMPLATE)
    assert len(findings) == 1
    assert findings[0].rule == "manual_dom_manipulation"


def test_standard_template_clean():
    findings = check_manual_dom_manipulation("", STANDARD_TEMPLATE)
    assert findings == []
