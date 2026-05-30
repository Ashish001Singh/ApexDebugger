# ApexDebugger — Salesforce Apex AI Code Reviewer

AI-powered reviewer for Salesforce Apex: governor-limit risk, bulkification, CRUD/FLS, SOQL injection, sharing mistakes.

## Phase 1 (current): Deterministic Rules
- SOQL in loop detection
- DML in loop detection
- Hardcoded ID detection
- Missing CRUD/FLS detection

## Quick start (Codespaces)

```bash
# Install deps
uv sync

# Review a file
uv run copilot review path/to/MyClass.cls

# Run tests
uv run pytest

# Run eval
uv run python eval/runner.py

# Start API
uv run uvicorn app:app --reload
```

## Project structure

```
src/apex_copilot/
  rules/       # Phase 1: deterministic regex/AST checks
  reasoning/   # Phase 2: LangGraph + Claude
  kb/          # Phase 3: SF docs scraping + embeddings
  retrieval/   # Phase 3: pgvector search
  review.py    # orchestration entrypoint
cli/main.py    # click CLI
eval/          # golden set + precision/recall scorer
tests/         # pytest
app.py         # FastAPI
```

## Phases

| Phase | What | Gate |
|-------|------|------|
| 1 | Deterministic rules + CLI | pytest green |
| 2 | LangGraph + Claude reasoning | eval precision ≥ 0.8 |
| 3 | SF docs KB + pgvector | LLM cites sources |
| 4 | SF org metadata | org-aware findings |
| 5 | VS Code extension | findings in editor |
