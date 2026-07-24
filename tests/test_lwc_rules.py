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


from src.lwc_copilot.rules.missing_wire_error_handler import check_missing_wire_error_handler

WIRE_NO_ERROR_HANDLER = """\
export default class Bad extends LightningElement {
    @wire(getContacts)
    contacts;
}"""

WIRE_WITH_ERROR_HANDLER = """\
export default class Good extends LightningElement {
    @wire(getContacts)
    wiredContacts({ data, error }) {
        if (data) {
            this.contacts = data;
        } else if (error) {
            this.error = error;
        }
    }
}"""


def test_wire_bare_property_detects():
    findings = check_missing_wire_error_handler(WIRE_NO_ERROR_HANDLER, "")
    assert len(findings) == 1
    assert findings[0].rule == "missing_wire_error_handler"


def test_wire_with_error_destructure_clean():
    findings = check_missing_wire_error_handler(WIRE_WITH_ERROR_HANDLER, "")
    assert findings == []


from src.lwc_copilot.rules.apex_call_in_loop import check_apex_call_in_loop

APEX_CALL_IN_LOOP = """\
import saveRecord from '@salesforce/apex/RecordController.saveRecord';

export default class Bad extends LightningElement {
    handleSaveAll(records) {
        for (const record of records) {
            saveRecord({ record });
        }
    }
}"""

APEX_CALL_OUTSIDE_LOOP = """\
import saveRecords from '@salesforce/apex/RecordController.saveRecords';

export default class Good extends LightningElement {
    handleSaveAll(records) {
        saveRecords({ records });
    }
}"""


def test_apex_call_in_loop_detects():
    findings = check_apex_call_in_loop(APEX_CALL_IN_LOOP, "")
    assert len(findings) == 1
    assert findings[0].rule == "apex_call_in_loop"


def test_apex_call_outside_loop_clean():
    findings = check_apex_call_in_loop(APEX_CALL_OUTSIDE_LOOP, "")
    assert findings == []
