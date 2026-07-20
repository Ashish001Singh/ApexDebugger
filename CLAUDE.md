# ApexDebugger — contributor & agent guide

AI-powered reviewer for Salesforce Apex: governor limits, bulkification, CRUD/FLS,
sharing, exception risk. Hybrid **deterministic rules + LLM reasoning**, gated by a
labeled golden eval set (the moat).

## Architecture

```
review(code)
  ├── run_all_rules(code)        deterministic regex rules — guaranteed recall floor
  └── run_reasoning_graph(...)   LangGraph: retrieve_context → reason → result
        retrieve_context         loads kb/best_practices.md (+ user doc) for grounding
        reason                   3 LLM calls → vote_findings → merge_findings
```

- **Deterministic layer** (`src/apex_copilot/rules/`): cheap, certain, 100% recall on its
  rules. Each rule is a pure function registered in `rules/registry.py`.
- **LLM layer** (`reasoning/graph.py`): finds reasoning-level issues regex can't
  (complexity, duplicate methods, exception risk). Runs blind (no findings fed in).
- **Voting** (`vote_findings`): 3 runs, keep findings in ≥2 — kills hallucination flicker.
- **Regex authority** (`REGEX_OWNED` + `merge_findings`): for rules the regex layer owns,
  the regex verdict wins; LLM claims on those are dropped. LLM keeps only reasoning rules.
- **Taxonomy** (`RuleId` enum in `reasoning/models.py`): controlled vocabulary shared by
  both layers — enables dedup and scoring.

## Conventions

- Imports use the `src.` prefix → run with `PYTHONPATH=.`.
- Run tests via the venv: `uv run python -m pytest` (not bare `uv run pytest`).
- LLM provider: OpenAI `gpt-4o-mini` (`config.py` / `.env`). Never hardcode keys.
- Grounding pays off on project/org-specific docs, NOT general SF knowledge the model
  already has. Keep `kb/best_practices.md` lean.

## Two evals, two jobs

- `eval/runner.py` — **deterministic** gate. Calls `run_all_rules` (regex only), free,
  same result every run. Skips LLM-only golden cases. This is the CI gate.
- `eval/llm_eval.py` — **probabilistic** eval. Calls `review()` N times, reports
  precision/recall/F1 + spread (variance). Costs money; run manually.

## Commands

```bash
uv sync --extra dev                          # install
PYTHONPATH=. uv run python -m pytest -m "not integration"   # unit tests (free)
PYTHONPATH=. uv run python eval/runner.py    # deterministic gate (free)
PYTHONPATH=. uv run python eval/llm_eval.py  # LLM eval (needs real key, costs $)
PYTHONPATH=. uv run copilot review File.cls  # CLI
```

## Testing rules

- Unit tests: pure functions (rules, `merge_findings`, `vote_findings`) — no API, run in CI.
- Integration tests: anything calling `review()`/the LLM — mark `@pytest.mark.integration`,
  excluded from CI (`-m "not integration"`), run manually with a real key.

## Adding a rule

1. Add the id to `RuleId` (`reasoning/models.py`).
2. Deterministic rule → pure function in `rules/`, register in `registry.py`, add to
   `REGEX_OWNED` in `graph.py`. LLM-only rule → just the `RuleId`; the LLM produces it.
3. Add a golden case in `eval/golden_set.jsonl` + a unit test.
