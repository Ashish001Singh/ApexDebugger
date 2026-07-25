"""
Integration tests for cross_reason — the LLM node that traces user input from an
LWC into unsafe dynamic SOQL/DML in the Apex it calls.

Marked @pytest.mark.integration: hits the real OpenAI API (costs money, non-
deterministic). Excluded from CI (-m "not integration"); run manually with a key.
"""
import pytest

from src.orchestrator.cross_reason import cross_reason, CrossPair
from src.review_core.models import RuleId


LWC_PASSES_TERM = """\
import search from '@salesforce/apex/LeadSearch.search';
export default class LeadFinder extends LightningElement {
    handleSearch(event) {
        search({ term: event.target.value });
    }
}"""

APEX_CONCATENATES = """\
public with sharing class LeadSearch {
    @AuraEnabled(cacheable=true)
    public static List<Lead> search(String term) {
        String q = 'SELECT Id, Name FROM Lead WHERE Name LIKE \\'%' + term + '%\\'';
        return Database.query(q);
    }
}"""

APEX_BINDS = """\
public with sharing class LeadSearch {
    @AuraEnabled(cacheable=true)
    public static List<Lead> search(String term) {
        String pattern = '%' + term + '%';
        return [SELECT Id, Name FROM Lead WHERE Name LIKE :pattern];
    }
}"""


@pytest.mark.integration
def test_flags_injection_when_input_concatenated():
    pair = CrossPair(
        lwc_file="leadFinder.js", lwc_js=LWC_PASSES_TERM,
        apex_file="LeadSearch.cls", apex_code=APEX_CONCATENATES,
    )
    findings = cross_reason([pair])

    rules = {f.rule.value for f in findings}
    assert RuleId.cross_language_injection_risk.value in rules   # BLANK 1: what rule MUST be present?


@pytest.mark.integration
def test_no_flag_when_input_bound():
    pair = CrossPair(
        lwc_file="leadFinder.js", lwc_js=LWC_PASSES_TERM,
        apex_file="LeadSearch.cls", apex_code=APEX_BINDS,
    )
    findings = cross_reason([pair])

    assert findings == []   # BLANK 2: the false-positive guard — what must be true of findings?
