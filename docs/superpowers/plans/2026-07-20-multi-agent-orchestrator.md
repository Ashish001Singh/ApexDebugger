# Multi-agent Orchestrator (Apex + LWC + Synthesizer) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend ApexDebugger to review LWC components (JS + HTML) alongside Apex, and consolidate findings from both into one report via a thin orchestrator.

**Architecture:** Extract the language-agnostic machinery (`Finding`/`Severity`/`RuleId`/`ReviewResult`, `vote_findings`, `merge_findings`, `LOOP_OPEN`) into a new `src/review_core/` package. Build a sibling `src/lwc_copilot/` package that mirrors `apex_copilot`'s shape (regex rules first, LLM reasoning second, same `REGEX_OWNED` split). A pure-code `src/orchestrator/` routes files by extension/bundle shape to the right reviewer(s) and flattens results — no LLM call of its own.

**Tech Stack:** Python 3.12, pydantic, LangGraph, OpenAI `gpt-4o-mini`, click, pytest.

## Global Constraints

- Imports use the `src.` prefix; run everything with `PYTHONPATH=.` (per [CLAUDE.md](../../../CLAUDE.md)).
- Run tests via `uv run python -m pytest` (not bare `uv run pytest`).
- Never hardcode API keys — `config.py` settings only, real keys in `.env`.
- No backwards-compatibility shims/re-exports for moved code — update every import site directly (per project convention).
- Unit tests: pure functions only, no API calls, run in CI (`-m "not integration"`).
- Integration tests: anything calling the LLM — `@pytest.mark.integration`, excluded from CI.
- RuleId is a single shared enum in `review_core/models.py` — Apex and LWC ids coexist there.
- `eval/runner.py` stays regex-only and free — it must never call an LLM.

---

## Part 1 — Extract `review_core` (pure refactor, no behavior change)

### Task 1: Move `Finding`/`Severity`/`RuleId`/`ReviewResult`/`LLMReviewOutput` to `review_core`

**Files:**
- Create: `src/review_core/__init__.py` (empty)
- Create: `src/review_core/models.py`
- Modify: `src/apex_copilot/reasoning/models.py` (delete — content moves out)
- Modify: `src/apex_copilot/reasoning/graph.py:29,35`
- Modify: `src/apex_copilot/review.py:2-3`
- Modify: `src/apex_copilot/retrieval/__init__.py:9`
- Modify: `src/apex_copilot/rules/missing_crud_fls.py:2`
- Modify: `src/apex_copilot/rules/registry.py:2`
- Modify: `src/apex_copilot/rules/soql_in_loop.py:2`
- Modify: `src/apex_copilot/rules/hardcoded_id.py:2`
- Modify: `src/apex_copilot/rules/dml_in_loop.py:2`
- Modify: `src/apex_copilot/rules/nested_loop.py:5`
- Modify: `cli/main.py:5`
- Modify: `tests/test_merge.py:1,3`
- Modify: `tests/test_runner_smoke.py:2`
- Modify: `tests/test_rules.py:6`
- Modify: `tests/test_vote.py:1,2,5`

**Interfaces:**
- Produces: `src.review_core.models.Severity`, `.RuleId`, `.Finding`, `.ReviewResult`, `.LLMReviewOutput` — identical shape to what `src.apex_copilot.reasoning.models` had.

- [ ] **Step 1: Run the full test suite to capture the pre-refactor baseline**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `23 passed, 2 deselected`

- [ ] **Step 2: Create `src/review_core/__init__.py`**

Empty file.

- [ ] **Step 3: Create `src/review_core/models.py` with the moved content**

```python
from enum import Enum
from pydantic import BaseModel


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RuleId(str, Enum):
    soql_in_loop = "soql_in_loop"
    dml_in_loop = "dml_in_loop"
    hardcoded_id = "hardcoded_id"
    hardcoded_external_id = "hardcoded_external_id"
    missing_crud_fls = "missing_crud_fls"
    missing_sharing_declaration = "missing_sharing_declaration"
    high_complexity = "high_complexity"
    duplicate_method = "duplicate_method"
    unbatched_db_calls = "unbatched_db_calls"
    missing_static_constant = "missing_static_constant"
    exception_risk = "exception_risk"
    best_practice_violation = "best_practice_violation"
    other = "other"
    explicit_system_mode = "explicit_system_mode"
    nested_loop_2 = "nested_loop_2"
    nested_loop_deep = "nested_loop_deep"
    # LWC rules
    unsafe_inner_html = "unsafe_inner_html"
    manual_dom_manipulation = "manual_dom_manipulation"
    imperative_apex_no_error_handling = "imperative_apex_no_error_handling"
    missing_wire_error_handler = "missing_wire_error_handler"
    apex_call_in_loop = "apex_call_in_loop"


class Finding(BaseModel):
    rule: RuleId
    severity: Severity
    line: int
    message: str
    suggestion: str
    doc_url: str | None = None


class ReviewResult(BaseModel):
    filename: str
    findings: list[Finding]
    summary: str | None = None
    llm_explanation: str | None = None


class LLMReviewOutput(BaseModel):
    findings: list[Finding]
    summary: str
```

- [ ] **Step 4: Delete `src/apex_copilot/reasoning/models.py`**

Run: `rm src/apex_copilot/reasoning/models.py`

- [ ] **Step 5: Update every import site**

In each file below, replace `from src.apex_copilot.reasoning.models import ...` with the same names imported `from src.review_core.models import ...`:

`src/apex_copilot/reasoning/graph.py` lines 29 and 35 collapse into one import:
```python
from src.review_core.models import Finding, ReviewResult, LLMReviewOutput, RuleId
```

`src/apex_copilot/review.py`:
```python
from src.apex_copilot.reasoning.graph import run_reasoning_graph
from src.review_core.models import ReviewResult
```

`src/apex_copilot/retrieval/__init__.py`:
```python
from src.review_core.models import Finding
```

`src/apex_copilot/rules/missing_crud_fls.py`:
```python
from src.review_core.models import Finding, Severity
```

`src/apex_copilot/rules/registry.py`:
```python
from src.review_core.models import Finding
```

`src/apex_copilot/rules/soql_in_loop.py`:
```python
from src.review_core.models import Finding, Severity
```

`src/apex_copilot/rules/hardcoded_id.py`:
```python
from src.review_core.models import Finding, Severity
```

`src/apex_copilot/rules/dml_in_loop.py`:
```python
from src.review_core.models import Finding, Severity
```

`src/apex_copilot/rules/nested_loop.py`:
```python
from src.review_core.models import Finding, Severity, RuleId
```

`cli/main.py`:
```python
from src.review_core.models import Severity
```

`tests/test_merge.py` (lines 1 and 3):
```python
from src.review_core.models import Finding
from src.apex_copilot.reasoning.graph import merge_findings
from src.review_core.models import Severity
```

`tests/test_runner_smoke.py` (line 2):
```python
from src.review_core.models import ReviewResult
```

`tests/test_rules.py` (line 6):
```python
from src.review_core.models import Severity
```

`tests/test_vote.py` (lines 1, 2, 5):
```python
from src.apex_copilot.reasoning.graph import vote_findings
from src.review_core.models import Finding, Severity
```
(and the duplicate import inside the test function on line 5 becomes `from src.review_core.models import Finding, Severity`)

- [ ] **Step 6: Register the new package for pytest/hatchling**

Modify `pyproject.toml` — add `"src/review_core"` to the wheel packages list:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/apex_copilot", "src/review_core", "cli"]
```

- [ ] **Step 7: Run the full test suite — must match the Step 1 baseline exactly**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `23 passed, 2 deselected`

- [ ] **Step 8: Commit**

```bash
git add src/review_core src/apex_copilot cli/main.py tests pyproject.toml
git commit -m "refactor: extract Finding/Severity/RuleId/ReviewResult into review_core"
```

---

### Task 2: Move `LOOP_OPEN` into `review_core`

**Files:**
- Create: `src/review_core/patterns.py`
- Modify: `src/apex_copilot/rules/patterns.py` (delete — content moves out)
- Modify: `src/apex_copilot/rules/soql_in_loop.py:3`
- Modify: `src/apex_copilot/rules/dml_in_loop.py:3`
- Modify: `src/apex_copilot/rules/nested_loop.py:7`

**Interfaces:**
- Consumes: nothing new.
- Produces: `src.review_core.patterns.LOOP_OPEN` — same compiled regex Task 1's baseline had in `apex_copilot/rules/patterns.py`.

- [ ] **Step 1: Read the current pattern to carry over exactly**

Run: `cat src/apex_copilot/rules/patterns.py`
(Confirms the current `LOOP_OPEN` regex — the one fixed for the nested-parens bug — carries over unchanged.)

- [ ] **Step 2: Create `src/review_core/patterns.py`**

```python
import re

# Matches a loop header up to its opening brace. Deliberately does NOT try to
# balance the parens in the condition (regex can't do that) — it matches
# everything up to the first `{`, so `while (i < list.size()) {` and
# `for (Integer i = 0; i < 3; i++) {` both match.
LOOP_OPEN = re.compile(r"\b(for|while)\b[^{]*\{|\bdo\b\s*\{", re.IGNORECASE)
```

(If the file read in Step 1 differs from this, use the file's actual current pattern instead — the point is a verbatim move, not a rewrite.)

- [ ] **Step 3: Delete `src/apex_copilot/rules/patterns.py`**

Run: `rm src/apex_copilot/rules/patterns.py`

- [ ] **Step 4: Update the three importers**

`src/apex_copilot/rules/soql_in_loop.py`, `dml_in_loop.py`, `nested_loop.py` — replace:
```python
from .patterns import LOOP_OPEN
```
with:
```python
from src.review_core.patterns import LOOP_OPEN
```

- [ ] **Step 5: Run the full test suite**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `23 passed, 2 deselected`

- [ ] **Step 6: Run the deterministic eval gate**

Run: `PYTHONPATH=. uv run python eval/runner.py`
Expected: `OVERALL [PASS]  Avg Precision: 1.00  Avg Recall: 1.00`

- [ ] **Step 7: Commit**

```bash
git add src/review_core/patterns.py src/apex_copilot/rules
git commit -m "refactor: move LOOP_OPEN into review_core"
```

---

### Task 3: Move `vote_findings` and `merge_findings` into `review_core`

**Files:**
- Create: `src/review_core/voting.py`
- Create: `src/review_core/merging.py`
- Modify: `src/apex_copilot/reasoning/graph.py` (remove the two function bodies, import instead)
- Modify: `tests/test_merge.py:2`
- Modify: `tests/test_vote.py:1`

**Interfaces:**
- Produces: `src.review_core.voting.vote_findings(runs: list[list[Finding]], threshold: int) -> list[Finding]`, `src.review_core.merging.merge_findings(regex: list[Finding], llm: list[Finding], regex_owned: set[RuleId]) -> list[Finding]` — note `merge_findings` gains a `regex_owned` parameter so it isn't hardcoded to Apex's `REGEX_OWNED` set (LWC will call it with its own set).

- [ ] **Step 1: Create `src/review_core/voting.py`**

```python
from collections import Counter
from src.review_core.models import Finding


def vote_findings(runs: list[list[Finding]], threshold: int) -> list[Finding]:
    """
    runs = N independent LLM finding-lists. Keep one representative Finding per
    RULE that appears in >= threshold of the runs. Kills random hallucinations.
    """
    rule_votes = Counter()
    representative = {}

    for run in runs:
        seen_this_run = set()
        for f in run:
            if f.rule not in representative:
                representative[f.rule] = f
            seen_this_run.add(f.rule)
        for rule in seen_this_run:
            rule_votes[rule] += 1

    return [representative[rule] for rule, votes in rule_votes.items() if votes >= threshold]
```

- [ ] **Step 2: Create `src/review_core/merging.py`**

```python
from src.review_core.models import Finding, RuleId


def merge_findings(
    regex: list[Finding], llm: list[Finding], regex_owned: set[RuleId]
) -> list[Finding]:
    seen = {(f.rule.value, f.line) for f in regex}

    extra_findings = list(regex)
    for f in llm:
        if f.rule in regex_owned:
            continue
        if (f.rule.value, f.line) in seen:
            continue
        extra_findings.append(f)

    return extra_findings
```

- [ ] **Step 3: Update `src/apex_copilot/reasoning/graph.py`**

Remove the `merge_findings` and `vote_findings` function definitions and the `from collections import Counter` import. Add:
```python
from src.review_core.voting import vote_findings
from src.review_core.merging import merge_findings
```

Update the one call site (inside `reason()`) to pass the module-level `REGEX_OWNED` set explicitly:
```python
    voted = vote_findings(runs, VOTE_THRESHOLD)
    merged_findings = merge_findings(state["findings"], voted, REGEX_OWNED)
```

- [ ] **Step 4: Update test imports**

`tests/test_merge.py` line 2:
```python
from src.review_core.merging import merge_findings
```
Every call site in that file passes 2 positional args today (`merge_findings(finding_regex, finding_llm)`); update every call to pass the Apex `REGEX_OWNED` set as the third argument:
```python
from src.apex_copilot.reasoning.graph import REGEX_OWNED
...
merged_findings = merge_findings(finding_regex, finding_llm, REGEX_OWNED)
```
Apply this same third-argument change to all 6 test functions in the file (`test_no_overlap`, `test_exact_overlap`, `test_no_llm_finding_rule_overlap`, `test_drops_llm_finding_on_regex_owned_rule`, `test_keeps_llm_finding_on_llm_owned_rule`, `test_llm_regex_owned_rule_dropped_even_at_different_line`, and the second `test_no_overlap`).

`tests/test_vote.py` line 1:
```python
from src.review_core.voting import vote_findings
```

- [ ] **Step 5: Run the full test suite**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `23 passed, 2 deselected`

- [ ] **Step 6: Commit**

```bash
git add src/review_core/voting.py src/review_core/merging.py src/apex_copilot/reasoning/graph.py tests/test_merge.py tests/test_vote.py
git commit -m "refactor: move vote_findings/merge_findings into review_core, parameterize regex_owned"
```

---

## Part 2 — LWC rules (regex layer)

### Task 4: Scaffold `lwc_copilot` package

**Files:**
- Create: `src/lwc_copilot/__init__.py` (empty)
- Create: `src/lwc_copilot/rules/__init__.py` (empty)
- Create: `src/lwc_copilot/rules/registry.py`
- Create: `src/lwc_copilot/reasoning/__init__.py` (empty)
- Modify: `pyproject.toml` wheel packages list

**Interfaces:**
- Produces: `src.lwc_copilot.rules.registry.run_all_rules(js_code: str, html_code: str) -> list[Finding]` — starts with an empty `RULES` list; Tasks 5-9 each append one rule.

- [ ] **Step 1: Create the empty `__init__.py` files**

```bash
touch src/lwc_copilot/__init__.py src/lwc_copilot/rules/__init__.py src/lwc_copilot/reasoning/__init__.py
```

- [ ] **Step 2: Create `src/lwc_copilot/rules/registry.py`**

```python
from typing import Callable
from src.review_core.models import Finding

RuleFunc = Callable[[str, str], list[Finding]]

RULES: list[RuleFunc] = []


def run_all_rules(js_code: str, html_code: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        findings.extend(rule(js_code, html_code))
    return findings
```

- [ ] **Step 3: Register the package in `pyproject.toml`**

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/apex_copilot", "src/review_core", "src/lwc_copilot", "cli"]
```

- [ ] **Step 4: Verify the package imports cleanly**

Run: `PYTHONPATH=. uv run python -c "from src.lwc_copilot.rules.registry import run_all_rules; print(run_all_rules('', ''))"`
Expected: `[]`

- [ ] **Step 5: Commit**

```bash
git add src/lwc_copilot pyproject.toml
git commit -m "feat(lwc): scaffold lwc_copilot package"
```

---

### Task 5: LWC rule — `unsafe_inner_html`

**Files:**
- Create: `src/lwc_copilot/rules/unsafe_inner_html.py`
- Test: `tests/test_lwc_rules.py` (new file — created here, extended by Tasks 6-9)
- Modify: `src/lwc_copilot/rules/registry.py`

**Interfaces:**
- Consumes: `Finding`, `Severity` from `src.review_core.models`.
- Produces: `check_unsafe_inner_html(js_code: str, html_code: str) -> list[Finding]`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_lwc_rules.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_rules.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.lwc_copilot.rules.unsafe_inner_html'`

- [ ] **Step 3: Write the rule**

Create `src/lwc_copilot/rules/unsafe_inner_html.py`:
```python
import re
from src.review_core.models import Finding, Severity

# .innerHTML = bypasses LWC's built-in XSS protection (textContent/lightning-formatted-text
# are auto-escaped; innerHTML is not). Flag any assignment, regardless of what's on the RHS —
# the safe alternative (textContent) exists for every legitimate use case.
_INNER_HTML_ASSIGN = re.compile(r"\.innerHTML\s*=(?!=)")


def check_unsafe_inner_html(js_code: str, html_code: str) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(js_code.splitlines(), start=1):
        if _INNER_HTML_ASSIGN.search(line):
            findings.append(
                Finding(
                    rule="unsafe_inner_html",
                    severity=Severity.HIGH,
                    line=lineno,
                    message="Direct innerHTML assignment bypasses LWC's built-in XSS protection.",
                    suggestion="Use textContent for text, or lightning-formatted-rich-text for sanitized HTML.",
                )
            )
    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_rules.py -v`
Expected: `2 passed`

- [ ] **Step 5: Wire it into the registry**

Modify `src/lwc_copilot/rules/registry.py`:
```python
from typing import Callable
from src.review_core.models import Finding
from .unsafe_inner_html import check_unsafe_inner_html

RuleFunc = Callable[[str, str], list[Finding]]

RULES: list[RuleFunc] = [
    check_unsafe_inner_html,
]


def run_all_rules(js_code: str, html_code: str) -> list[Finding]:
    findings: list[Finding] = []
    for rule in RULES:
        findings.extend(rule(js_code, html_code))
    return findings
```

- [ ] **Step 6: Run the full suite**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `25 passed, 2 deselected`

- [ ] **Step 7: Commit**

```bash
git add src/lwc_copilot/rules/unsafe_inner_html.py src/lwc_copilot/rules/registry.py tests/test_lwc_rules.py
git commit -m "feat(lwc): unsafe_inner_html rule"
```

---

### Task 6: LWC rule — `manual_dom_manipulation`

**Files:**
- Create: `src/lwc_copilot/rules/manual_dom_manipulation.py`
- Modify: `tests/test_lwc_rules.py`
- Modify: `src/lwc_copilot/rules/registry.py`

**Interfaces:**
- Produces: `check_manual_dom_manipulation(js_code: str, html_code: str) -> list[Finding]` — this is the first rule that reads the `html_code` argument.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_lwc_rules.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_rules.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.lwc_copilot.rules.manual_dom_manipulation'`

- [ ] **Step 3: Write the rule**

Create `src/lwc_copilot/rules/manual_dom_manipulation.py`:
```python
import re
from src.review_core.models import Finding, Severity

# lwc:dom="manual" opts an element OUT of LWC's synthetic shadow DOM management,
# meaning the framework's diffing/reconciliation no longer applies to it — bugs
# from direct DOM writes on that subtree are the developer's responsibility.
_MANUAL_DOM = re.compile(r'lwc:dom\s*=\s*"manual"')


def check_manual_dom_manipulation(js_code: str, html_code: str) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(html_code.splitlines(), start=1):
        if _MANUAL_DOM.search(line):
            findings.append(
                Finding(
                    rule="manual_dom_manipulation",
                    severity=Severity.MEDIUM,
                    line=lineno,
                    message='lwc:dom="manual" opts this element out of LWC\'s DOM management.',
                    suggestion="Confirm this is intentional (e.g. third-party widget mount point). Prefer declarative templating where possible.",
                )
            )
    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_rules.py -v`
Expected: `4 passed`

- [ ] **Step 5: Wire it into the registry**

Modify `src/lwc_copilot/rules/registry.py` — add the import and append to `RULES`:
```python
from .manual_dom_manipulation import check_manual_dom_manipulation

RULES: list[RuleFunc] = [
    check_unsafe_inner_html,
    check_manual_dom_manipulation,
]
```

- [ ] **Step 6: Run the full suite**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `27 passed, 2 deselected`

- [ ] **Step 7: Commit**

```bash
git add src/lwc_copilot/rules/manual_dom_manipulation.py src/lwc_copilot/rules/registry.py tests/test_lwc_rules.py
git commit -m "feat(lwc): manual_dom_manipulation rule"
```

---

### Task 7: LWC rule — `imperative_apex_no_error_handling`

**Files:**
- Create: `src/lwc_copilot/rules/imperative_apex_no_error_handling.py`
- Modify: `tests/test_lwc_rules.py`
- Modify: `src/lwc_copilot/rules/registry.py`

**Interfaces:**
- Produces: `check_imperative_apex_no_error_handling(js_code: str, html_code: str) -> list[Finding]`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_lwc_rules.py`:
```python
from src.lwc_copilot.rules.imperative_apex_no_error_handling import (
    check_imperative_apex_no_error_handling,
)

IMPERATIVE_NO_CATCH = """\
import getContacts from '@salesforce/apex/ContactController.getContacts';

export default class Bad extends LightningElement {
    handleClick() {
        getContacts()
            .then((result) => {
                this.contacts = result;
            });
    }
}"""

IMPERATIVE_WITH_CATCH = """\
import getContacts from '@salesforce/apex/ContactController.getContacts';

export default class Good extends LightningElement {
    handleClick() {
        getContacts()
            .then((result) => {
                this.contacts = result;
            })
            .catch((error) => {
                this.error = error;
            });
    }
}"""


def test_imperative_call_without_catch_detects():
    findings = check_imperative_apex_no_error_handling(IMPERATIVE_NO_CATCH, "")
    assert len(findings) == 1
    assert findings[0].rule == "imperative_apex_no_error_handling"


def test_imperative_call_with_catch_clean():
    findings = check_imperative_apex_no_error_handling(IMPERATIVE_WITH_CATCH, "")
    assert findings == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_rules.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the rule**

Create `src/lwc_copilot/rules/imperative_apex_no_error_handling.py`:
```python
import re
from src.review_core.models import Finding, Severity

# Names imported from '@salesforce/apex/...' are imperative Apex call wrappers.
_APEX_IMPORT = re.compile(
    r"^\s*import\s+(\w+)\s+from\s+['\"]@salesforce/apex/", re.MULTILINE
)
_THEN_CALL = re.compile(r"\.then\s*\(")
_CATCH_CALL = re.compile(r"\.catch\s*\(")

# How many lines after a bare `.then(` we scan for a matching `.catch(` before
# concluding there isn't one. Generous enough to cover a multi-line arrow
# function body, small enough to stay a per-statement check.
_CATCH_LOOKAHEAD_LINES = 8


def check_imperative_apex_no_error_handling(js_code: str, html_code: str) -> list[Finding]:
    apex_names = set(_APEX_IMPORT.findall(js_code))
    if not apex_names:
        return []

    findings: list[Finding] = []
    lines = js_code.splitlines()

    for lineno, line in enumerate(lines, start=1):
        called_name = None
        for name in apex_names:
            if re.search(rf"\b{re.escape(name)}\s*\(", line):
                called_name = name
                break
        if called_name is None:
            continue

        window = "\n".join(lines[lineno - 1 : lineno - 1 + _CATCH_LOOKAHEAD_LINES])
        if _THEN_CALL.search(window) and not _CATCH_CALL.search(window):
            findings.append(
                Finding(
                    rule="imperative_apex_no_error_handling",
                    severity=Severity.MEDIUM,
                    line=lineno,
                    message=f"Imperative Apex call '{called_name}' has no .catch() error handler.",
                    suggestion="Add a .catch() block (or try/catch with await) to surface Apex errors to the user.",
                )
            )

    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_rules.py -v`
Expected: `6 passed`

- [ ] **Step 5: Wire it into the registry**

Modify `src/lwc_copilot/rules/registry.py`:
```python
from .imperative_apex_no_error_handling import check_imperative_apex_no_error_handling

RULES: list[RuleFunc] = [
    check_unsafe_inner_html,
    check_manual_dom_manipulation,
    check_imperative_apex_no_error_handling,
]
```

- [ ] **Step 6: Run the full suite**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `29 passed, 2 deselected`

- [ ] **Step 7: Commit**

```bash
git add src/lwc_copilot/rules/imperative_apex_no_error_handling.py src/lwc_copilot/rules/registry.py tests/test_lwc_rules.py
git commit -m "feat(lwc): imperative_apex_no_error_handling rule"
```

---

### Task 8: LWC rule — `missing_wire_error_handler`

**Files:**
- Create: `src/lwc_copilot/rules/missing_wire_error_handler.py`
- Modify: `tests/test_lwc_rules.py`
- Modify: `src/lwc_copilot/rules/registry.py`

**Interfaces:**
- Produces: `check_missing_wire_error_handler(js_code: str, html_code: str) -> list[Finding]`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_lwc_rules.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_rules.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the rule**

Create `src/lwc_copilot/rules/missing_wire_error_handler.py`:
```python
import re
from src.review_core.models import Finding, Severity

# @wire followed by a bare property (`contacts;`) with no destructure at all
# means data AND error both go unhandled — data lands in `this.contacts`
# implicitly with no error path. A wired FUNCTION with `{ data, error }`
# params is the pattern that handles errors; anything else, flag it.
_WIRE_DECORATOR = re.compile(r"@wire\([^)]*\)\s*\n?\s*(\w+)\s*(\(([^)]*)\))?\s*[;{]")


def check_missing_wire_error_handler(js_code: str, html_code: str) -> list[Finding]:
    findings: list[Finding] = []

    for match in _WIRE_DECORATOR.finditer(js_code):
        params = match.group(3)
        lineno = js_code[: match.start()].count("\n") + 1

        has_error_param = params is not None and "error" in params
        if not has_error_param:
            findings.append(
                Finding(
                    rule="missing_wire_error_handler",
                    severity=Severity.MEDIUM,
                    line=lineno,
                    message="@wire property/function has no 'error' handling — failed requests fail silently.",
                    suggestion="Wire to a function with `({ data, error })` params and handle both branches.",
                )
            )

    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_rules.py -v`
Expected: `8 passed`

- [ ] **Step 5: Wire it into the registry**

Modify `src/lwc_copilot/rules/registry.py`:
```python
from .missing_wire_error_handler import check_missing_wire_error_handler

RULES: list[RuleFunc] = [
    check_unsafe_inner_html,
    check_manual_dom_manipulation,
    check_imperative_apex_no_error_handling,
    check_missing_wire_error_handler,
]
```

- [ ] **Step 6: Run the full suite**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `31 passed, 2 deselected`

- [ ] **Step 7: Commit**

```bash
git add src/lwc_copilot/rules/missing_wire_error_handler.py src/lwc_copilot/rules/registry.py tests/test_lwc_rules.py
git commit -m "feat(lwc): missing_wire_error_handler rule"
```

---

### Task 9: LWC rule — `apex_call_in_loop`

**Files:**
- Create: `src/lwc_copilot/rules/apex_call_in_loop.py`
- Modify: `tests/test_lwc_rules.py`
- Modify: `src/lwc_copilot/rules/registry.py`

**Interfaces:**
- Consumes: `LOOP_OPEN` from `src.review_core.patterns` (Task 2's output — `for`/`while`/`do` header up to `{`, works identically on JS since both languages share C-family loop syntax).
- Produces: `check_apex_call_in_loop(js_code: str, html_code: str) -> list[Finding]`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_lwc_rules.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_rules.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the rule**

Create `src/lwc_copilot/rules/apex_call_in_loop.py`:
```python
import re
from src.review_core.models import Finding, Severity
from src.review_core.patterns import LOOP_OPEN

_APEX_IMPORT = re.compile(
    r"^\s*import\s+(\w+)\s+from\s+['\"]@salesforce/apex/", re.MULTILINE
)


def check_apex_call_in_loop(js_code: str, html_code: str) -> list[Finding]:
    apex_names = set(_APEX_IMPORT.findall(js_code))
    if not apex_names:
        return []

    findings: list[Finding] = []
    lines = js_code.splitlines()

    in_loop_depth: list[int] = []
    brace_depth = 0

    for lineno, line in enumerate(lines, start=1):
        open_braces = line.count("{")
        close_braces = line.count("}")

        if LOOP_OPEN.search(line):
            in_loop_depth.append(brace_depth + open_braces)

        brace_depth += open_braces - close_braces
        in_loop_depth = [d for d in in_loop_depth if brace_depth >= d]

        if in_loop_depth:
            for name in apex_names:
                if re.search(rf"\b{re.escape(name)}\s*\(", line):
                    findings.append(
                        Finding(
                            rule="apex_call_in_loop",
                            severity=Severity.HIGH,
                            line=lineno,
                            message=f"Imperative Apex call '{name}' inside a loop — one server round-trip per iteration.",
                            suggestion="Batch the records into a single call (accept a List param on the Apex side) outside the loop.",
                        )
                    )

    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_rules.py -v`
Expected: `10 passed`

- [ ] **Step 5: Wire it into the registry**

Modify `src/lwc_copilot/rules/registry.py`:
```python
from .apex_call_in_loop import check_apex_call_in_loop

RULES: list[RuleFunc] = [
    check_unsafe_inner_html,
    check_manual_dom_manipulation,
    check_imperative_apex_no_error_handling,
    check_missing_wire_error_handler,
    check_apex_call_in_loop,
]
```

- [ ] **Step 6: Run the full suite**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `33 passed, 2 deselected`

- [ ] **Step 7: Commit**

```bash
git add src/lwc_copilot/rules/apex_call_in_loop.py src/lwc_copilot/rules/registry.py tests/test_lwc_rules.py
git commit -m "feat(lwc): apex_call_in_loop rule"
```

---

## Part 3 — LWC LLM layer + review()

### Task 10: `lwc_copilot` reasoning graph (LLM layer)

**Files:**
- Create: `src/lwc_copilot/reasoning/graph.py`
- Test: `tests/test_lwc_runner_smoke.py` (new, integration-marked)

**Interfaces:**
- Consumes: `vote_findings`, `merge_findings` from `review_core` (Task 3); `Finding`, `ReviewResult`, `LLMReviewOutput`, `RuleId` from `review_core.models` (Task 1).
- Produces: `run_reasoning_graph(js_code: str, html_code: str, findings: list[Finding], filename: str) -> ReviewResult`, and `REGEX_OWNED: set[RuleId]` (LWC's own set — used by Task 12's registry wiring and by `merge_findings`).

- [ ] **Step 1: Write the failing integration test**

Create `tests/test_lwc_runner_smoke.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_runner_smoke.py -v -m integration`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.lwc_copilot.reasoning.graph'`

- [ ] **Step 3: Write the graph**

Create `src/lwc_copilot/reasoning/graph.py`:
```python
SYSTEM_PROMPT = """
You are a 15 year Salesforce Architect specializing in Lightning Web Components.
Review the given LWC JavaScript (and template HTML, if provided) for:
1. Security: unsafe DOM writes that bypass LWC's built-in XSS protection.
2. Apex integration: imperative calls missing error handling, @wire usage that
   swallows errors, patterns that cause repeated server round-trips.
3. General LWC anti-patterns: reactive property misuse, missing null checks on
   wired data before use, event handling that could throw.

Make sure to check the line clearly — we merge these findings with a regex
layer, so line numbers must point at the exact offending line in the JS
source (not the HTML template, unless the finding is specifically about the
template).

Do NOT report innerHTML issues if only textContent is used. Do NOT report a
missing .catch() if one is present on the same call chain. Only report what
you can point to a specific line for.
"""

from src.review_core.models import Finding, ReviewResult, LLMReviewOutput, RuleId
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from config import settings
from openai import OpenAI
from src.review_core.voting import vote_findings
from src.review_core.merging import merge_findings

REGEX_OWNED = {
    RuleId.unsafe_inner_html,
    RuleId.manual_dom_manipulation,
    RuleId.imperative_apex_no_error_handling,
    RuleId.missing_wire_error_handler,
    RuleId.apex_call_in_loop,
}

client = OpenAI(api_key=settings.openai_api_key)

VOTE_RUNS = 3
VOTE_THRESHOLD = 2


class LwcReviewState(TypedDict):
    js_code: str
    html_code: str
    filename: str
    findings: list[Finding]
    summary: str | None
    llm_explanation: str | None


def run_reasoning_graph(
    js_code: str, html_code: str, findings: list[Finding], filename: str
) -> ReviewResult:
    initial_state = {
        "js_code": js_code,
        "html_code": html_code,
        "filename": filename,
        "findings": findings,
        "summary": None,
        "llm_explanation": None,
    }
    final_state = graph.invoke(initial_state)

    return ReviewResult(
        filename=filename,
        findings=final_state["findings"],
        summary=final_state["summary"],
        llm_explanation=final_state["llm_explanation"],
    )


def reason(state: LwcReviewState) -> dict:
    user_message = f"""Review this LWC component.

Filename: {state['filename']}

JavaScript:
{state['js_code']}

Template HTML:
{state['html_code']}

Explain why each finding matters and rate overall risk."""

    runs = []
    summary = None
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
        output = response.choices[0].message.parsed
        runs.append(output.findings)
        if summary is None:
            summary = output.summary

    voted = vote_findings(runs, VOTE_THRESHOLD)
    merged_findings = merge_findings(state["findings"], voted, REGEX_OWNED)
    return {
        "findings": merged_findings,
        "summary": summary,
        "llm_explanation": "\n".join(
            f" - [line {f.line}] {f.rule.value}: {f.message}" for f in merged_findings
        ),
    }


builder = StateGraph(LwcReviewState)
builder.add_node("reason", reason)
builder.add_edge(START, "reason")
builder.add_edge("reason", END)

graph = builder.compile()
```

- [ ] **Step 4: Run the integration test manually (costs money — run once to confirm wiring, not part of CI)**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_runner_smoke.py -v -m integration`
Expected: `1 passed` (requires a real `OPENAI_API_KEY` in `.env`)

- [ ] **Step 5: Confirm the unit suite (which excludes this test) still passes**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `33 passed, 3 deselected`

- [ ] **Step 6: Commit**

```bash
git add src/lwc_copilot/reasoning/graph.py tests/test_lwc_runner_smoke.py
git commit -m "feat(lwc): LangGraph reasoning layer for LWC review"
```

---

### Task 11: `lwc_copilot.review()`

**Files:**
- Create: `src/lwc_copilot/review.py`
- Modify: `tests/test_lwc_runner_smoke.py`

**Interfaces:**
- Consumes: `run_all_rules` (Task 9's registry), `run_reasoning_graph` (Task 10).
- Produces: `review(js_code: str, html_code: str = "", filename: str = "anonymous.js") -> ReviewResult` — the public entrypoint the orchestrator (Task 13) calls.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_lwc_runner_smoke.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_runner_smoke.py -v -m integration`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.lwc_copilot.review'`

- [ ] **Step 3: Write `review.py`**

Create `src/lwc_copilot/review.py`:
```python
from src.lwc_copilot.rules.registry import run_all_rules
from src.lwc_copilot.reasoning.graph import run_reasoning_graph
from src.review_core.models import ReviewResult


def review(js_code: str, html_code: str = "", filename: str = "anonymous.js") -> ReviewResult:
    """Main LWC entrypoint. Takes JS (+ optional template HTML), returns structured ReviewResult."""
    findings = run_all_rules(js_code, html_code)
    result = run_reasoning_graph(js_code, html_code, findings, filename)
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_lwc_runner_smoke.py -v -m integration`
Expected: `2 passed`

- [ ] **Step 5: Confirm the unit suite still passes**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `33 passed, 3 deselected`

- [ ] **Step 6: Commit**

```bash
git add src/lwc_copilot/review.py tests/test_lwc_runner_smoke.py
git commit -m "feat(lwc): review() entrypoint"
```

---

## Part 4 — Orchestrator

### Task 12: `orchestrator.route`

**Files:**
- Create: `src/orchestrator/__init__.py` (empty)
- Create: `src/orchestrator/route.py`
- Test: `tests/test_orchestrator.py` (new file — extended by Task 13)

**Interfaces:**
- Produces: `route(paths: list[Path]) -> RoutedFiles` where `RoutedFiles` is a small dataclass with `apex_files: list[Path]` and `lwc_bundles: list[LwcBundle]` (`LwcBundle` = dataclass with `js: Path`, `html: Path | None`), plus `skipped: list[Path]` for unknown extensions.

- [ ] **Step 1: Write the failing test**

Create `tests/test_orchestrator.py`:
```python
from pathlib import Path
from src.orchestrator.route import route


def test_routes_apex_file(tmp_path):
    cls_file = tmp_path / "Foo.cls"
    cls_file.write_text("public class Foo {}")

    result = route([cls_file])

    assert result.apex_files == [cls_file]
    assert result.lwc_bundles == []
    assert result.skipped == []


def test_routes_lwc_bundle_with_html_sibling(tmp_path):
    bundle_dir = tmp_path / "myComponent"
    bundle_dir.mkdir()
    js_file = bundle_dir / "myComponent.js"
    html_file = bundle_dir / "myComponent.html"
    js_file.write_text("export default class MyComponent {}")
    html_file.write_text("<template></template>")

    result = route([js_file])

    assert result.apex_files == []
    assert len(result.lwc_bundles) == 1
    assert result.lwc_bundles[0].js == js_file
    assert result.lwc_bundles[0].html == html_file


def test_routes_lwc_js_without_html_sibling(tmp_path):
    js_file = tmp_path / "orphan.js"
    js_file.write_text("export default class Orphan {}")

    result = route([js_file])

    assert len(result.lwc_bundles) == 1
    assert result.lwc_bundles[0].html is None


def test_skips_unknown_extension(tmp_path):
    unknown_file = tmp_path / "notes.txt"
    unknown_file.write_text("hello")

    result = route([unknown_file])

    assert result.apex_files == []
    assert result.lwc_bundles == []
    assert result.skipped == [unknown_file]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_orchestrator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.orchestrator'`

- [ ] **Step 3: Write `route.py`**

Create `src/orchestrator/__init__.py` (empty), then `src/orchestrator/route.py`:
```python
from dataclasses import dataclass, field
from pathlib import Path

APEX_EXTENSIONS = {".cls", ".trigger"}
LWC_JS_EXTENSION = ".js"


@dataclass
class LwcBundle:
    js: Path
    html: Path | None


@dataclass
class RoutedFiles:
    apex_files: list[Path] = field(default_factory=list)
    lwc_bundles: list[LwcBundle] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)


def route(paths: list[Path]) -> RoutedFiles:
    result = RoutedFiles()

    for path in paths:
        if path.suffix in APEX_EXTENSIONS:
            result.apex_files.append(path)
        elif path.suffix == LWC_JS_EXTENSION:
            html_sibling = path.with_suffix(".html")
            result.lwc_bundles.append(
                LwcBundle(js=path, html=html_sibling if html_sibling.exists() else None)
            )
        else:
            result.skipped.append(path)

    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_orchestrator.py -v`
Expected: `4 passed`

- [ ] **Step 5: Run the full unit suite**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `37 passed, 3 deselected`

- [ ] **Step 6: Commit**

```bash
git add src/orchestrator tests/test_orchestrator.py
git commit -m "feat(orchestrator): route files to apex/lwc by extension and bundle shape"
```

---

### Task 13: `orchestrator.synthesize`

**Files:**
- Create: `src/orchestrator/synthesize.py`
- Modify: `tests/test_orchestrator.py`

**Interfaces:**
- Consumes: `ReviewResult` from `review_core.models`.
- Produces: `synthesize(results: list[ReviewResult]) -> list[ReviewResult]` — pure code, sorts each result's findings by severity (HIGH → MEDIUM → LOW → INFO), returns the input list unchanged in structure (one `ReviewResult` per file — flattening happens at the CLI print layer in Task 14, which already prints per-file). No LLM call.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_orchestrator.py`:
```python
from src.orchestrator.synthesize import synthesize
from src.review_core.models import ReviewResult, Finding, Severity


def _finding(rule, severity, line):
    return Finding(rule=rule, severity=severity, line=line, message="x", suggestion="y")


def test_synthesize_sorts_findings_by_severity_within_each_result():
    result = ReviewResult(
        filename="Foo.cls",
        findings=[
            _finding("missing_sharing_declaration", Severity.INFO, 1),
            _finding("dml_in_loop", Severity.HIGH, 5),
            _finding("nested_loop_2", Severity.MEDIUM, 3),
        ],
    )

    synthesized = synthesize([result])

    assert len(synthesized) == 1
    severities = [f.severity for f in synthesized[0].findings]
    assert severities == [Severity.HIGH, Severity.MEDIUM, Severity.INFO]


def test_synthesize_preserves_one_result_per_file():
    apex_result = ReviewResult(filename="Foo.cls", findings=[])
    lwc_result = ReviewResult(filename="bar.js", findings=[])

    synthesized = synthesize([apex_result, lwc_result])

    filenames = [r.filename for r in synthesized]
    assert filenames == ["Foo.cls", "bar.js"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_orchestrator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.orchestrator.synthesize'`

- [ ] **Step 3: Write `synthesize.py`**

Create `src/orchestrator/synthesize.py`:
```python
from src.review_core.models import ReviewResult, Severity

_SEVERITY_ORDER = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2, Severity.INFO: 3}


def synthesize(results: list[ReviewResult]) -> list[ReviewResult]:
    """Pure consolidation: sort each result's findings by severity. No LLM call."""
    for result in results:
        result.findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity, 99))
    return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. uv run python -m pytest tests/test_orchestrator.py -v`
Expected: `6 passed`

- [ ] **Step 5: Run the full unit suite**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `39 passed, 3 deselected`

- [ ] **Step 6: Commit**

```bash
git add src/orchestrator/synthesize.py tests/test_orchestrator.py
git commit -m "feat(orchestrator): synthesize — sort findings by severity, pure code"
```

---

## Part 5 — CLI + eval wiring

### Task 14: Extend `copilot review` to route multi-file / mixed-language input

**Files:**
- Modify: `cli/main.py`

**Interfaces:**
- Consumes: `route` (Task 12), `synthesize` (Task 13), `apex_copilot.review.review`, `lwc_copilot.review.review`.
- Produces: no new public interface — this is the terminal CLI task; behavior is verified manually.

- [ ] **Step 1: Read the current CLI to confirm the exact block being replaced**

Run: `cat cli/main.py`
(Confirms the current single-argument `@click.argument("file", ...)` signature from earlier in this session.)

- [ ] **Step 2: Rewrite `cli/main.py`**

```python
import sys
import json
from pathlib import Path
import click
from src.review_core.models import Severity
from src.orchestrator.route import route
from src.orchestrator.synthesize import synthesize
from src.apex_copilot.review import review as apex_review_fn
from src.lwc_copilot.review import review as lwc_review_fn


@click.group()
def cli() -> None:
    """ApexDebugger — Salesforce Apex + LWC AI Code Reviewer."""


@cli.command()
@click.argument("files", type=click.Path(exists=True, readable=True), nargs=-1, required=True)
@click.option("--json-output", is_flag=True, help="Output findings as JSON.")
@click.option("--min-severity", default="low", type=click.Choice(["low", "medium", "high"]))
def apex_review(files: tuple[str, ...], json_output: bool, min_severity: str) -> None:
    """Review one or more Apex .cls/.trigger or LWC .js FILES for issues."""
    paths = [Path(f) for f in files]
    routed = route(paths)

    for skipped in routed.skipped:
        click.secho(f"Skipping {skipped} — unrecognized extension.", fg="yellow")

    results = []
    for apex_path in routed.apex_files:
        code = apex_path.read_text()
        results.append(apex_review_fn(code, filename=str(apex_path)))
    for bundle in routed.lwc_bundles:
        js_code = bundle.js.read_text()
        html_code = bundle.html.read_text() if bundle.html else ""
        results.append(lwc_review_fn(js_code, html_code, filename=str(bundle.js)))

    results = synthesize(results)

    severity_order = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2, Severity.INFO: -1}
    min_level = severity_order.get(Severity(min_severity), 0)

    has_high = False
    for result in results:
        filtered = [f for f in result.findings if severity_order.get(f.severity, 0) >= min_level]

        if json_output:
            click.echo(json.dumps([f.model_dump() for f in filtered], indent=2))
            continue

        if not filtered:
            click.secho(f"{result.filename}: no issues found.", fg="green")
            continue

        click.echo(f"\nReviewing: {result.filename}")
        click.echo(f"Found {len(filtered)} issue(s):\n")

        for finding in filtered:
            color = {"high": "red", "medium": "yellow", "low": "cyan"}.get(finding.severity.value, "white")
            click.secho(
                f"  [{finding.severity.value.upper()}] Line {finding.line} — {finding.rule.value}",
                fg=color,
                bold=True,
            )
            click.echo(f"    {finding.message}")
            click.secho(f"    Fix: {finding.suggestion}", fg="blue")
            click.echo()

        if any(f.severity == Severity.HIGH for f in filtered):
            has_high = True

    sys.exit(1 if has_high else 0)


cli.add_command(apex_review, name="review")
```

- [ ] **Step 3: Verify existing single-Apex-file behavior is unchanged**

Run: `PYTHONPATH=. uv run copilot review examples/BadOrderProcessor.cls`
Expected: same findings as before (soql_in_loop, dml_in_loop, nested_loop_2, nested_loop_deep, etc.)

- [ ] **Step 4: Verify mixed-file routing works (manual smoke test)**

Run: `PYTHONPATH=. uv run copilot review examples/BadOrderProcessor.cls examples/InsecureLeadHandler.cls`
Expected: two `Reviewing: ...` sections printed, one per file.

- [ ] **Step 5: Run the full unit suite**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `39 passed, 3 deselected`

- [ ] **Step 6: Commit**

```bash
git add cli/main.py
git commit -m "feat(cli): route multi-file/mixed-language input through orchestrator"
```

---

### Task 15: Eval — `lang` field + LWC golden cases

**Files:**
- Modify: `eval/golden_set.jsonl` (add `"lang": "apex"` to every existing line; add 5 new LWC cases)
- Modify: `eval/runner.py`

**Interfaces:**
- No new public interface — `run_eval()` behavior changes to route by `lang`.

- [ ] **Step 1: Add `"lang": "apex"` to every existing golden_set.jsonl line**

Run this one-off script to rewrite the file (each existing line gets `"lang": "apex"` appended before the closing brace):
```bash
python3 -c "
import json
from pathlib import Path

p = Path('eval/golden_set.jsonl')
lines = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
for case in lines:
    case['lang'] = 'apex'
p.write_text('\n'.join(json.dumps(c) for c in lines) + '\n')
"
```

- [ ] **Step 2: Append 5 LWC golden cases**

Append these 5 lines to `eval/golden_set.jsonl` (one JSON object per line):
```
{"id": "unsafe_inner_html_001", "description": "Direct innerHTML assignment", "lang": "lwc", "js": "export default class Bad extends LightningElement {\n    renderedCallback() {\n        this.template.querySelector('div').innerHTML = this.raw;\n    }\n}", "html": "", "expected_rules": ["unsafe_inner_html"]}
{"id": "manual_dom_manipulation_001", "description": "lwc:dom=manual in template", "lang": "lwc", "js": "", "html": "<template>\n    <div lwc:dom=\"manual\"></div>\n</template>", "expected_rules": ["manual_dom_manipulation"]}
{"id": "imperative_apex_no_error_handling_001", "description": "Imperative call with .then() but no .catch()", "lang": "lwc", "js": "import getContacts from '@salesforce/apex/ContactController.getContacts';\n\nexport default class Bad extends LightningElement {\n    handleClick() {\n        getContacts()\n            .then((result) => {\n                this.contacts = result;\n            });\n    }\n}", "html": "", "expected_rules": ["imperative_apex_no_error_handling"]}
{"id": "missing_wire_error_handler_001", "description": "@wire to bare property, no error handling", "lang": "lwc", "js": "export default class Bad extends LightningElement {\n    @wire(getContacts)\n    contacts;\n}", "html": "", "expected_rules": ["missing_wire_error_handler"]}
{"id": "apex_call_in_loop_001", "description": "Imperative Apex call inside a for loop", "lang": "lwc", "js": "import saveRecord from '@salesforce/apex/RecordController.saveRecord';\n\nexport default class Bad extends LightningElement {\n    handleSaveAll(records) {\n        for (const record of records) {\n            saveRecord({ record });\n        }\n    }\n}", "html": "", "expected_rules": ["apex_call_in_loop"]}
```

- [ ] **Step 3: Update `eval/runner.py` to route by `lang`**

Replace the full file:
```python
"""
Eval runner: loads golden_set.jsonl, runs the regex-only layer for each
case's language, scores precision + recall.

Usage:
    uv run python eval/runner.py

Gate: precision >= 0.8 AND recall >= 0.8 across all graded cases.
"""

"""
  Two evals, two jobs, two functions they call:
    runner.py    → run_all_rules  → "are my regex rules correct?"   (free, deterministic)
    llm_eval.py  → review         → "is the whole product good?"    (paid, probabilistic)
"""
import json
from pathlib import Path
from src.apex_copilot.rules import run_all_rules as run_apex_rules
from src.lwc_copilot.rules.registry import run_all_rules as run_lwc_rules

APEX_REGEX_RULES = {"soql_in_loop", "dml_in_loop", "hardcoded_id", "hardcoded_external_id",
                     "missing_crud_fls", "missing_sharing_declaration", "explicit_system_mode",
                     "nested_loop_2", "nested_loop_deep"}

LWC_REGEX_RULES = {"unsafe_inner_html", "manual_dom_manipulation",
                    "imperative_apex_no_error_handling", "missing_wire_error_handler",
                    "apex_call_in_loop"}

GOLDEN_SET = Path(__file__).parent / "golden_set.jsonl"
GATE_PRECISION = 0.8
GATE_RECALL = 0.8


def score_case(expected_rules: list[str], found_rules: list[str]) -> tuple[float, float]:
    expected = set(expected_rules)
    found = set(found_rules)
    tp = len(expected & found)
    precision = tp / len(found) if found else 0.0
    recall = tp / len(expected) if expected else 0.0
    return precision, recall


def run_eval() -> None:
    cases = [json.loads(line) for line in GOLDEN_SET.read_text().splitlines() if line.strip()]

    total_precision, total_recall = 0.0, 0.0
    print(f"\nRunning eval on {len(cases)} golden cases\n{'='*50}")
    graded = 0
    for case in cases:
        lang = case.get("lang", "apex")
        regex_rules = APEX_REGEX_RULES if lang == "apex" else LWC_REGEX_RULES

        if not set(case["expected_rules"]) <= regex_rules:
            continue
        graded += 1

        if lang == "apex":
            found_rules = [f.rule.value for f in run_apex_rules(case["code"])]
        else:
            found_rules = [f.rule.value for f in run_lwc_rules(case.get("js", ""), case.get("html", ""))]

        precision, recall = score_case(case["expected_rules"], found_rules)
        total_precision += precision
        total_recall += recall

        status = "PASS" if precision >= GATE_PRECISION and recall >= GATE_RECALL else "FAIL"
        print(f"[{status}] {case['id']}")
        print(f"  Expected: {case['expected_rules']}")
        print(f"  Found:    {found_rules}")
        print(f"  Precision: {precision:.2f}  Recall: {recall:.2f}\n")

    avg_p = total_precision / graded if graded else 0.0
    avg_r = total_recall / graded if graded else 0.0
    overall = "PASS" if avg_p >= GATE_PRECISION and avg_r >= GATE_RECALL else "FAIL"
    print(f"{'='*50}")
    print(f"OVERALL [{overall}]  Avg Precision: {avg_p:.2f}  Avg Recall: {avg_r:.2f}")
    print(f"Gate: precision >= {GATE_PRECISION}, recall >= {GATE_RECALL}")

    if overall == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    run_eval()
```

- [ ] **Step 4: Run the deterministic eval gate**

Run: `PYTHONPATH=. uv run python eval/runner.py`
Expected: `OVERALL [PASS]  Avg Precision: 1.00  Avg Recall: 1.00` across 15 graded cases (10 apex + 5 lwc)

- [ ] **Step 5: Run the full unit suite one more time**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q`
Expected: `39 passed, 3 deselected`

- [ ] **Step 6: Commit**

```bash
git add eval/golden_set.jsonl eval/runner.py
git commit -m "feat(eval): route deterministic gate by lang, add 5 LWC golden cases"
```

---

## Part 6 — Wrap-up

### Task 16: Journal + README + push

**Files:**
- Modify: `docs/learning-journal.md`
- Modify: `README.md`

**Interfaces:** none — documentation only.

- [ ] **Step 1: Append a journal entry**

Append to `docs/learning-journal.md` (format: Q → Why/Reasoning → Principle):
```markdown
## Multi-agent orchestrator: Apex + LWC + synthesizer

**Q: Why extract `review_core` instead of copy-pasting Finding/Severity/RuleId/vote_findings/merge_findings into a new `lwc_copilot` package?**

**Why/Reasoning:** The machinery (voting, merging, the Finding/Severity shape) is
language-agnostic — it operates on `list[Finding]` regardless of whether the
findings came from Apex or LWC rules. Copy-pasting it would mean every future
bug fix (like the nested-parens LOOP_OPEN fix) has to be applied twice and can
silently drift. `RuleId` stays a SINGLE shared enum (not per-language) so the
orchestrator's `synthesize()` never has to reconcile two vocabularies, and
`merge_findings`/`vote_findings` don't need language-specific variants — they
just take a `regex_owned` set as a parameter now instead of importing a
hardcoded one.

**Principle:** Extract shared machinery into its own package when two
consumers need identical behavior, not just similar behavior. Don't extract
things that only look similar today but might legitimately diverge (that's
why LWC got its own `rules/` and `reasoning/graph.py` — the actual rule
logic and prompts are genuinely different per language, so those stayed
separate).

**Q: Why does `orchestrator.route()` group `.js` files with a sibling `.html` instead of requiring the LWC bundle folder as input?**

**Why/Reasoning:** LWC components are folders (`myComponent/myComponent.js` +
`.html` + meta files), but CI/PR tooling typically hands you a flat list of
changed file paths, not folders. Routing by "does a `.html` file with the
same stem exist next to this `.js` file" works with both a single file path
and a folder walk, and degrades gracefully (LWC bundle with no HTML sibling
still gets JS-only checks — the `manual_dom_manipulation` rule just returns
no findings since it has nothing to scan).

**Principle:** Design the router around the shape of input you'll actually
receive (individual changed file paths from a PR diff), not the shape that's
architecturally "cleaner" (a bundle folder) but harder to get from the
calling context.
```

- [ ] **Step 2: Update README roadmap**

Modify `README.md` roadmap table:
```markdown
| Multi-agent orchestrator (Apex + LWC reviewers → synthesizer) | ✅ |
| Org-metadata grounding (schema, FLS, sharing) — the org-aware moat | planned |
| Interprocedural analysis (method-in-loop DML), VS Code extension | planned |
```

- [ ] **Step 3: Run the full suite + eval one final time**

Run: `PYTHONPATH=. uv run python -m pytest -m "not integration" -q && PYTHONPATH=. uv run python eval/runner.py`
Expected: `39 passed, 3 deselected` then `OVERALL [PASS]  Avg Precision: 1.00  Avg Recall: 1.00`

- [ ] **Step 4: Commit and push**

```bash
git add docs/learning-journal.md README.md
git commit -m "docs: journal entry + roadmap update for multi-agent orchestrator"
git push -u origin <branch-name>
```

- [ ] **Step 5: Open a PR**

```bash
gh pr create --title "Multi-agent orchestrator: Apex + LWC reviewers + synthesizer" --body "See docs/superpowers/specs/2026-07-20-multi-agent-orchestrator-design.md for design, docs/superpowers/plans/2026-07-20-multi-agent-orchestrator.md for implementation plan."
```
