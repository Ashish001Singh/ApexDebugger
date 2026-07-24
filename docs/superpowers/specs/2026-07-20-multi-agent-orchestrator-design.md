# Multi-agent orchestrator: Apex + LWC reviewers → synthesizer

## Goal

Extend ApexDebugger beyond Apex to review LWC components (JS/HTML), and
consolidate findings from both languages into one report per PR/file-set.
Apex reviewer stays first-class and unchanged in behavior for existing users.

## Architecture

```
copilot review <path>...
  → orchestrator.route(files)          # by extension/bundle shape
  → apex_copilot.review(f)  for each .cls / .trigger
  → lwc_copilot.review(f)   for each LWC bundle (.js + sibling .html)
  → orchestrator.synthesize(results)   # pure code: flatten, sort by severity
  → CLI prints combined report
```

## Package layout

```
src/review_core/
    models.py     Severity, RuleId (single shared enum — apex_* and lwc_* ids
                   coexist here), Finding, ReviewResult, LLMReviewOutput
    voting.py      vote_findings (moved as-is from apex_copilot/reasoning/graph.py,
                   already generic over list[Finding])
    merging.py     merge_findings (moved as-is, already generic)

src/apex_copilot/
    rules/         unchanged, imports Finding/RuleId/Severity from review_core
    reasoning/graph.py   apex-specific prompts + its REGEX_OWNED set, imports
                   voting/merging from review_core
    review.py       unchanged public signature: review(code, filename) -> ReviewResult

src/lwc_copilot/
    rules/          new pure-function rules (regex-first, same shape as apex_copilot/rules/):
                     - unsafe_inner_html.py      (innerHTML assignment)
                     - manual_dom_manipulation.py (lwc:dom="manual" in template)
                     - imperative_apex_no_error_handling.py (imperative call, no .catch/try-catch)
                     - missing_wire_error_handler.py (@wire with no error param handled)
                     - apex_call_in_loop.py       (imperative Apex call inside a loop — client-side governor-limit-adjacent)
    reasoning/graph.py   lwc-specific prompts + its own REGEX_OWNED set, same
                   retrieve_context → reason → result shape as apex_copilot's graph
    review.py       review(code, html, filename) -> ReviewResult (needs both
                   JS and template to check lwc:dom="manual")

src/orchestrator/
    route.py        group input paths into apex_files / lwc_bundles (dir grouping
                   by parent folder + sibling .html), skip+warn on unknown extensions
    synthesize.py    pure code: flatten list[ReviewResult] → single combined
                   result, sort findings by severity, no LLM call
```

## RuleId taxonomy

Single shared `RuleId` enum in `review_core/models.py`. New LWC members added
alongside existing Apex ones (naming finalized during implementation):
`unsafe_inner_html`, `manual_dom_manipulation`,
`imperative_apex_no_error_handling`, `missing_wire_error_handler`,
`apex_call_in_loop`.

One enum (not per-language) because: single controlled vocabulary, no
reconciliation needed in `synthesize()`, and `vote_findings`/`merge_findings`
already operate generically on `list[Finding]` — a shared enum keeps that
machinery genuinely shared rather than parameterized per language.

## Rule detection layer

Same hybrid pattern as Apex: regex rules first (free, certain, guaranteed
recall floor for patterns that are syntactically definite — `innerHTML =`,
`lwc:dom="manual"`, imperative call with no adjacent `.catch`/try-catch).
LLM layer (blind, no findings fed in) covers judgment calls: whether
bulkification was actually needed, whether wire vs. imperative was the right
choice for the use case. `REGEX_OWNED` + `merge_findings` split applies
identically to LWC: regex verdict authoritative for rules regex owns, LLM
claims on those dropped.

## CLI

`copilot review <path>...` (existing command, extended):
- accepts one or more paths (currently single-file only)
- routes each by extension/bundle shape via `orchestrator.route`
- Apex-only input: behaves exactly as today (single apex_copilot.review call,
  no orchestrator/synthesize overhead — avoids changing existing single-file
  Apex behavior)
- LWC or mixed input: runs relevant reviewer(s), synthesizes, prints combined
  report using the existing per-finding format (already tagged by filename)

## Eval

`eval/golden_set.jsonl` gets a `lang` field (`apex` | `lwc`) per case, same
file, same `eval/runner.py` — routes each case to the right `review()` by
`lang`, still regex-only, still free, still the CI gate. Avoids maintaining
two parallel eval pipelines; matches the shared-`review_core` direction.

LWC test corpus for manual/exploratory testing (not committed):
`/Users/ashishsinghmacair/Desktop/ASCENT/force-app/main/default/lwc/` — real
components, local use only, never copied into this public repo
(client/work code — confidentiality).

## Error handling

- Unknown file extension passed to `route()`: warn, skip, don't crash the run.
- LWC bundle missing its `.html` sibling: `manual_dom_manipulation` check
  (needs the template) is skipped for that file with a note in the finding
  set; JS-only checks still run.

## Testing

- LWC rules: pure-function unit tests, same pattern as
  `tests/test_nested_loop.py` — no API calls, CI-eligible.
- `orchestrator.route` / `orchestrator.synthesize`: pure unit tests using
  fake `Finding`/`ReviewResult` objects — no mocking of `review()` internals,
  no LLM, CI-eligible.
- `lwc_copilot.review()` (calls the LLM): `@pytest.mark.integration`, same
  exclusion (`-m "not integration"`) as today.

## Out of scope (this phase)

- Cross-language reasoning in the synthesizer (e.g. linking an Apex method
  missing sharing enforcement to the LWC component calling it without error
  handling). Synthesizer is pure consolidation only — flatten, dedupe, sort.
  Revisit once both single-language reviewers are proven.
- Org-metadata grounding (schema/FLS/sharing) — already deferred, separate
  roadmap item.
