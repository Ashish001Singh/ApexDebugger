# ApexDebugger — hybrid AI code reviewer for Salesforce Apex

An agentic code reviewer that catches governor-limit risks, security gaps (CRUD/FLS,
sharing), and design smells in Apex — built as a **deterministic rules engine + LLM
reasoning layer**, gated by a labeled golden eval set with F1 scoring.

Built by a Salesforce architect (8 yrs, 13 certs incl. Sharing & Visibility Architect)
encoding real review judgment into a measurable AI system.

```mermaid
flowchart LR
    A[Apex code] --> B["Deterministic rules<br/>regex · free · 100% recall"]
    A --> C[LangGraph loop]
    C --> D[retrieve grounding]
    D --> E["3× LLM calls"]
    E --> F["vote ≥2/3<br/>drop hallucinations"]
    B --> G["merge<br/>regex authority"]
    F --> G
    G --> H["ReviewResult<br/>CLI · API · CI"]
```

## Why hybrid — the core design decision

| | Deterministic rules | LLM reasoning |
|---|---|---|
| Catches | SOQL/DML in loops, hardcoded IDs, CRUD/FLS, sharing, nesting depth | complexity, duplicate methods, exception risk — what regex *can't* see |
| Reliability | 100%, every run | probabilistic (measured, see eval) |
| Cost | free, instant | metered API calls |

**Objective checks live in the certain layer; judgment calls go to the LLM.** A reviewer
that "usually" catches governor-limit bugs is worthless — the deterministic floor is what
lets this tool make a guarantee.

## Reliability engineering on the LLM layer

- **Blind independent review** — the LLM never sees the regex findings (no anchoring;
  it's a genuine second reviewer, not a rubber stamp).
- **Consensus voting** — 3 independent runs, keep findings appearing in ≥2. Random
  hallucinations flicker between runs; real findings are stable. Measured effect:
  run-to-run variance (spread) collapsed to ~0 on most golden cases.
- **Regex authority** — for rule types the deterministic layer owns, its verdict is
  final; LLM claims on those are dropped. Kills *stable* hallucinations voting can't.
- **Controlled vocabulary** — a shared `RuleId` enum forces both layers to speak the
  same language, making findings dedupable and scoreable.

## The eval is the product

Every finding type is scored against a hand-labeled golden set (`eval/golden_set.jsonl`)
— review judgment frozen into data.

- `eval/runner.py` — **deterministic gate**: regex layer vs golden labels. Free,
  reproducible, runs in CI on every PR. Currently 10/10 cases at 1.00 precision/recall.
- `eval/llm_eval.py` — **probabilistic eval**: full pipeline, N runs per case, reports
  mean F1 **and spread**. Spread doubles as a diagnostic: low spread + low score =
  deterministic bug (fix the code); high spread = LLM noise (fix the prompt).
- Grounding was **A/B tested** (with/without): general SF best practices gave zero lift
  (the model already knows them) — so grounding effort targets project/org-specific docs,
  where the model has a genuine knowledge gap.

## What it catches

Governor limits (SOQL/DML in loops), hardcoded record & external IDs, missing CRUD/FLS
enforcement (all API v56+ syntaxes: `WITH USER_MODE`, `WITH SECURITY_ENFORCED`,
`as user/system`, `AccessLevel.*`), missing sharing declarations, explicit system-mode
bypasses, nested-loop depth (CPU/heap risk), duplicate methods, exception risk,
complexity — full taxonomy in `RuleId` (`src/apex_copilot/reasoning/models.py`).

Reviews can be grounded on **your own team's conventions**: point
`USER_BEST_PRACTICES_PATH` at a project-specific markdown doc.

## Quick start

```bash
uv sync --extra dev
export OPENAI_API_KEY=sk-...                        # .env also works

PYTHONPATH=. uv run copilot review path/to/MyClass.cls    # review a file
PYTHONPATH=. uv run python -m pytest -m "not integration" # unit tests (free)
PYTHONPATH=. uv run python eval/runner.py                 # deterministic gate (free)
PYTHONPATH=. uv run python eval/llm_eval.py               # full LLM eval (costs $)
PYTHONPATH=. uv run uvicorn app:app --reload              # POST /review API
```

## Repo map

```
src/apex_copilot/
  rules/         deterministic checks — one pure function per rule + registry
  reasoning/     LangGraph graph, RuleId taxonomy, voting + merge logic
  kb/            best-practices grounding doc (small-corpus RAG)
eval/            golden set + deterministic runner + LLM eval (F1 + spread)
tests/           unit (CI) + integration (manual, marked)
cli/ · app.py    click CLI · FastAPI endpoint
docs/            learning-journal.md — the reasoning behind every design decision
.github/         CI: unit tests + deterministic eval gate on every PR
```

## Roadmap

| Stage | Status |
|---|---|
| Deterministic rules engine + CLI | ✅ |
| LangGraph reasoning, structured output, taxonomy | ✅ |
| Voting, regex authority, F1 eval + variance diagnostics | ✅ |
| Best-practices grounding (A/B measured) + user-supplied docs | ✅ |
| CI gate (tests + deterministic eval) | ✅ |
| Review-on-PR GitHub Action | ✅ |
| Multi-agent orchestrator (Apex + LWC reviewers → synthesizer) | ✅ |
| Cross-language synthesizer (LLM: LWC↔Apex contract bugs) | 🔜 |
| Org-metadata grounding (schema, FLS, sharing) — the org-aware moat | planned |
| Interprocedural analysis (method-in-loop DML), VS Code extension | planned |

## Design notes

The full reasoning — every tradeoff, why each layer exists, what the A/B tests showed —
is in [docs/learning-journal.md](docs/learning-journal.md).
