"""
rollup: a single advisory LLM pass over ALL findings in a run. Not a gate — it
produces a short prose summary that names the top risks and groups related
findings into root causes. Gated: only runs when the run has enough findings to
be worth summarizing.
"""
from openai import OpenAI
from config import settings
from src.review_core.models import ReviewResult

client = OpenAI(api_key=settings.openai_api_key)
ROLLUP_MIN_FINDINGS = 3          # below this, a summary adds nothing


SYSTEM_PROMPT = """You are a senior Salesforce reviewer writing the one-paragraph summary at the top of a code review.

You are given a flat list of findings already detected in this pull request — one per line, as: file | rule | line | message.

Your job: help the reader see the forest, not re-list the trees.
- Name the top 2-3 risks, most severe first.
- Where several findings share one root cause, say so and group them (e.g. "SOQL-in-loop appears in 5 places — one missing bulkification pattern, not five bugs").
- Be specific and short: 2-4 sentences of prose, no bullet dump, no restating every finding.
- Write for an engineer deciding what to fix first.

Hard rule: summarize ONLY the findings given. Do NOT invent issues, rules, or files that are not in the list. If the findings are unrelated, say they are unrelated rather than forcing a theme."""


def _digest(results: list[ReviewResult]) -> str:
    """Flatten every finding to one compact line the model can reason over."""
    lines = []
    for r in results:
        for f in r.findings:
            # BLANK 2: one line per finding — what does the model need to see
            # a theme? (file, rule, line, message — enough to group, not the code)
            lines.append(f"{r.filename} | {f.rule.value} | line {f.line} | {f.message}")
    return "\n".join(lines)


def rollup(results: list[ReviewResult]) -> str | None:
    total = sum(len(r.findings) for r in results)                    # BLANK 1: count findings across all results
    if total < ROLLUP_MIN_FINDINGS:
        return None                # gated — not worth a call

    response = client.chat.completions.create(
        model=settings.openai_model,
        max_tokens=400,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _digest(results)},
        ],
    )
    return response.choices[0].message.content.strip()