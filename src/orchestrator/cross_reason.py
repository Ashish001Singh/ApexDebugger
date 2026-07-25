"""
cross_reason: LLM node that reasons over an (LWC, Apex-it-calls) pair to find
data-flow bugs no single-file review can see — e.g. user input from the LWC
reaching unsafe dynamic SOQL/DML in the Apex (injection across the seam).
"""
from dataclasses import dataclass
from openai import OpenAI
from config import settings
from src.review_core.models import Finding, LLMReviewOutput
from src.review_core.voting import vote_findings

client = OpenAI(api_key=settings.openai_api_key)
VOTE_RUNS = 3
VOTE_THRESHOLD = 2


@dataclass
class CrossPair:
    lwc_file: str
    lwc_js: str
    apex_file: str
    apex_code: str


SYSTEM_PROMPT = """
You are a Salesforce Security Architect with 15+ years of experience. Review the provided Apex and LWC code only for cross-language injection vulnerabilities.

Detect only cases where untrusted input is embedded into another language or interpreter without proper validation, encoding, escaping, or parameterization.

Check for:
- Dynamic SOQL/SOSL injection
- DML

Make sure to check the line clearly and don't deflect from the actual line because we are merging all the findings together so
it is very important that line should be considered clearly.

Do NOT flag when the query is parameterized or sanitized: a bind variable
(WHERE x = :var), String.escapeSingleQuotes(input), or a static [SELECT ...]
with no string building. Only flag when untrusted LWC input is concatenated
into a dynamic query string.

CRITICAL — value-side vs query-side concatenation. Concatenation that builds a
VALUE which is then passed as a bind variable is SAFE, not injection:
    String pattern = '%' + term + '%';
    return [SELECT Id FROM Lead WHERE Name LIKE :pattern];
The user input never enters the query string — it is bound. Do NOT flag this.
Only flag concatenation into the query STRING ITSELF, e.g. text passed to
Database.query()/Database.getQueryLocator():
    String q = 'SELECT Id FROM Lead WHERE Name LIKE \\'%' + term + '%\\'';
    return Database.query(q);   // ← untrusted input in the query text = injection
"""


def _reason_one(pair: CrossPair) -> list[Finding]:
    user_message = f"""Analyze this LWC and the Apex it calls for injection across the boundary.

LWC ({pair.lwc_file}):
{pair.lwc_js}

Apex ({pair.apex_file}):
{pair.apex_code}

Report cross_language_injection_risk only if user input flows into unsafe dynamic SOSL/SOQL/DML."""

    runs = []
    for _ in range(VOTE_RUNS):
        response = client.chat.completions.parse(
            model=settings.openai_model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format=LLMReviewOutput,
        )
        runs.append(response.choices[0].message.parsed.findings)

    # BLANK 2: collapse the 3 runs into agreed findings (kill flicker).
    voted = vote_findings(runs, VOTE_THRESHOLD)
    # keep ONLY the injection rule (the LLM might mention others; not our job here)
    return [f for f in voted if f.rule.value == "cross_language_injection_risk"]


def cross_reason(pairs: list[CrossPair]) -> list[Finding]:
    findings: list[Finding] = []
    for pair in pairs:
        findings.extend(_reason_one(pair))
    return findings