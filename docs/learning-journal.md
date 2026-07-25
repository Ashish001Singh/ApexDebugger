# ApexDebugger — Learning Journal

A running record of the **concepts** and **why** behind ApexDebugger — the agentic-AI
engineering decisions, in Q&A form. Skips the transient stuff (specific bugs, code
snippets, test runs); keeps the reasoning worth remembering.

Format: **Q** (the question, mine or implied) · **Why / Reasoning** · **Principle** (the
one-line takeaway).

---

## 1. Architecture: deterministic rules + LLM

**Q: If the LLM can find governor-limit / security issues too, why keep the regex rules?**
Why: A regex finds `soql_in_loop` 100% of the time, in 0 ms, for free. The LLM finds it
~90% of the time, costs money, and is slow. For an *objective* check, non-determinism is a
bug. The deterministic layer is the guarantee you can *promise* ("we catch every X"); that
promise is sellable. "AI-powered, usually works" is not.
**Principle:** Certain + pattern-matchable → deterministic. Needs judgment/context → LLM.
Put the certain things in the certain layer.

**Q: Why run the deterministic rules BEFORE the LLM, not after?**
Why: Cheap, exact gates first; expensive probabilistic brain only on what's left. Same as
Salesforce validation rules before an approval process, or UPI PIN-format check before the
fraud ML model. You never pay the LLM for what a regex already caught.
**Principle:** Order layers by cost × certainty — cheapest & most certain first.

---

## 2. The agent loop (LangGraph)

**Q: Why a graph/state machine instead of one function calling the LLM?**
Why: Each node owns one job (retrieve → reason → result) and stamps its part of a shared
"ticket" (state), like a Swiggy order moving through kitchen stations, or an SObject through
an approval process. Separation makes each step testable and swappable per phase.
**Principle:** Model a pipeline as nodes over shared state; each node reads/writes only its part.

**Q: Why does a node return only the keys it changed, not the whole state?**
Why: LangGraph does a partial merge. Returning a full state risks clobbering fields other
nodes set. Return your delta; the framework merges.
**Principle:** Emit deltas, not full state — avoids accidental overwrites.

**Q: Why build `ReviewResult` outside the graph, and why is `.compile()` needed?**
Why: Nodes return dict deltas, not domain objects — so the final object is assembled after
`.invoke()`. `.compile()` validates the wiring (reachable nodes, START→END path) and freezes
it — same as Apex compile-on-save catching a bad reference before runtime.
**Principle:** Validate/freeze the graph before running; assemble domain objects at the edge.

---

## 3. The LLM as an independent reviewer

**Q: The LLM just parroted the findings we fed it. Why?**
Why: We handed it the answer key ("rules found X, Y") — so it copied instead of reasoning.
**Principle:** Don't feed a model the answers you want it to independently produce.

**Q: So why review "blind" (code only, no findings)?**
Why: A blind LLM is an *independent second reviewer* — its overlap with regex is high-
confidence, its unique finds are the reasoning-level issues regex can't do. Like a two-person
code review where reviewer B reviews cold instead of rubber-stamping A's notes.
**Principle:** Independent reviews catch more than sequential ones that see each other's work.

---

## 4. Structured output + controlled vocabulary

**Q: Why force the LLM into a typed schema instead of free text?**
Why: You can't *score* a paragraph. Eval needs `found_rules` vs `expected_rules` as typed
sets. Free text = "Database Calls Optimization" for what regex calls `soql_in_loop` — same
bug, unscoreable. Structured output is the bridge from "sounds smart" to "measurably right."
**Principle:** If you must evaluate it, structure it.

**Q: Why a `RuleId` enum (controlled vocabulary) shared by both layers?**
Why: A picklist, not a free-text field. Without it, regex and LLM speak different words for
the same issue → can't dedup, can't score. The enum is a *contract* — it even caught a rule
we emitted that wasn't registered.
**Principle:** Shared controlled vocabulary is what makes multi-source findings comparable.

---

## 5. Merging & de-duplication

**Q: Why dedup in code instead of asking another LLM to merge?**
Why: Dedup is objective ("is (rule, line) already present?") — one correct answer. An LLM
deduper costs money, adds latency, and is non-deterministic, which would make the *eval*
unstable. Reshape the problem down to an `if`, then use an `if`.
**Principle:** Don't send a deterministic decision to a probabilistic tool.

**Q: Why did the line-drift dedup problem stop mattering?**
Why: Once regex and LLM own *disjoint* rule sets (see §7 Fix B), they can't collide on
(rule, line) at all. A design change dissolved the problem instead of solving it.
**Principle:** Sometimes you engineer the problem away rather than handle it.

---

## 6. Evaluation — the moat

**Q: Where does "expected" come from? How does the system know the right answer?**
Why: It doesn't — *you* label it, from expertise. The golden set is judgment frozen into
data — like `System.assertEquals(expected, actual)` where you wrote `expected`. The model is
rented; the answer key is owned. That's the moat.
**Principle:** The labeled eval set is the product no competitor can copy.

**Q: Why precision, recall, AND F1?**
Why: Precision punishes false alarms; recall punishes misses; F1 balances both in one number.
**Principle:** One metric hides a tradeoff; name both sides, then combine.

**Q: Why run the LLM eval N times and measure *spread*, not just the mean?**
Why: One LLM run is one ball faced, not a strike rate. The LLM wobbles; the mean over N runs
is its real ability, and the *spread* is whether you can trust it. Bonus: spread diagnoses
failure type — **low spread + low score = deterministic bug** (fixable for sure);
**high spread = LLM noise** (tighten prompt / accept variance).
**Principle:** For probabilistic systems, measure the distribution, not a point. Variance is a diagnostic.

**Q: An eval "didn't improve" after a change — does that mean the change was useless?**
Why: Not necessarily — the eval may not *exercise* the thing you changed. After Fix B dropped
the LLM's regex-owned findings, the golden set (mostly regex-owned) became blind to LLM/
grounding changes until reasoning-rule cases were added.
**Principle:** An eval only measures what its cases exercise. Improve a component → add cases that depend on it.

---

## 7. Reliability: voting + regex authority

**Q: Can we run the LLM multiple times and use agreement?**
Why: Yes — self-consistency. Run N times *independently*, keep findings in ≥ threshold runs.
Hallucinations flicker (different each run); real findings are stable. Like requiring multiple
approvers — the outlier doesn't pass. (But feeding prior findings back = anchoring trap; keep
runs independent.)
**Principle:** Consensus across independent runs filters random error; never feed a model its own prior output.

**Q: After voting, a hallucination still survived. Why, and what fixes it?**
Why: A *stable* (consistent) hallucination isn't random, so voting can't kill it. But if it's
on a rule the regex layer *owns* and regex correctly said "no," the regex verdict is
authoritative — drop the LLM's claim (Fix B / `REGEX_OWNED`). The LLM keeps only rules regex
can't do.
**Principle:** For rules the deterministic layer owns, deterministic wins; the LLM adds value only where regex can't reach.

**Q: KNOWN LIMITATION — if regex has a *coverage gap* (a real `soql_in_loop` in a syntax the
regex doesn't parse) and the LLM catches it, Fix B drops it. Isn't that a lost finding?**
Why: Yes — a genuine miss disappears. It's the accepted cost of regex authority. Note first:
regex scans the whole file, so it never catches one instance of a pattern and misses another
of the *same* syntax — the gap only exists for syntax *variants* the rule doesn't cover. We
can't safely keep "new-location" LLM findings to patch this, because line drift plus the LLM's
tendency to hallucinate regex-owned rules make a real regex-gap catch indistinguishable from
an invented one. So the safety net *moves*: instead of "LLM rescues at runtime" (unreliable),
it becomes "eval surfaces the gap → you extend the regex" (reliable, permanent) — exactly how
`as user` / `as system` / `WITH SYSTEM_MODE` coverage was added.
**Principle:** Don't patch a deterministic hole with a probabilistic layer — it lets non-determinism back in. Close the gap in the deterministic rule; let the eval find the gaps.

---

## 8. Grounding / RAG

**Q: MCP vs RAG — do we need MCP to fetch best practices?**
Why: No — different things. MCP = a protocol to expose *tools*. RAG = fetching *docs* to
ground the model. You can build RAG with zero MCP.
**Principle:** Don't adopt a technology because it's adjacent; match the tool to the need.

**Q: Vector DB + embeddings, or just load the doc into the prompt?**
Why: If the corpus fits the context window, stuff it in (cheapest). Switch to embeddings +
vector search only when it *exceeds* the context window (also cost/noise). Small config →
load it all; you don't build a query optimizer for 10 rows.
**Principle:** Context-stuff small corpora; retrieve only when size forces it.

**Q: We added grounding and the eval passed — done, right?**
Why: No — a single ("ON") measurement has no counterfactual (post-hoc fallacy). The A/B
(grounding OFF) showed *identical* results: the model already knew general SF best practices,
so grounding gave zero lift. Grounding pays off only on what the model *can't* know — your
project conventions, your org's schema.
**Principle:** Always A/B (control vs treatment) before attributing an effect. Ground only on what the model doesn't already know.

---

## 9. Provider & cost discipline

**Q: Why OpenAI here, and does the provider matter?**
Why: Chosen for available credits; the architecture (prompts, eval, graph, taxonomy) is
provider-agnostic — swapping models is a small SDK change. The *skill* is provider-independent.
**Principle:** Build provider-agnostic; the moat is your prompts + eval, not the vendor.

**Q: How do we improve quality without burning money?**
Why: Prove logic with free unit tests (pure functions need no API). Spend on the eval only to
*confirm*, and A/B a single isolated case before a full run.
**Principle:** Validate for free first; pay only to confirm.

---

## 10. CI, tests, and gates

**Q: Why is the deterministic eval the CI gate but the LLM eval is not?**
Why: A CI gate must be **deterministic + free + fast**. The LLM eval is **probabilistic +
costs money + slow** — it would flake (fail good PRs by chance), bankrupt the pipeline, and
need a stored secret. A flaky gate is worse than none (people ignore red).
**Principle:** CI gates must be deterministic; probabilistic checks are manual tools.

**Q: Why split unit vs integration tests?**
Why: Unit tests are pure logic (free, fast, in CI). Integration tests hit a real service
(LLM) — slow, cost money, need credentials — so they're marked and excluded from the free CI
run, executed manually. Same as mock-callout vs live-callout tests in a deploy pipeline.
**Principle:** Keep external-service tests out of the fast free gate; mark and run them separately.

---

## 11. Multi-agent orchestration (planned: + LWC reviewer)

**Q: To add an LWC reviewer alongside Apex, what's the right architecture?**
Why: The orchestrator-workers pattern — a **router** inspects the changed files and routes by
type (`.cls` → Apex agent, `.js/.html` → LWC agent); the specialist agents run independently
(can be parallel); a **synthesizer** consolidates their findings into one report. It's an
evolution, not a rewrite: `review()` becomes the orchestrator, the current Apex pipeline
becomes one worker, `merge_findings` grows into the synthesizer. Each agent keeps its own
rules + LLM prompt + golden eval set (the moat scales per language). Sequence: finish Apex
first, then add LWC — don't restructure for a feature not yet built (YAGNI).
**Principle:** Grow single-purpose pipelines into multi-agent systems by promoting existing pieces (entry → router, pipeline → worker, merge → synthesizer), not rewriting.

**Q: Is the synthesizer code or an LLM?**
Why: Depends on the job. *Consolidating + deduping* findings is objective → code (same as
`merge_findings`). *Cross-language contract* reasoning — e.g. "this LWC `@wire`s an Apex method
that has no CRUD check" — needs judgment neither single-language agent has → LLM. Start with
code-consolidation; the cross-cutting LLM synthesizer is the high-value v2 (finds boundary
bugs no single-file linter can).
**Principle:** Same rule as everywhere — objective consolidation → code; cross-context reasoning → LLM.

---

## 12. Multi-agent orchestrator (built: Apex + LWC + synthesizer)

**Q: Why extract a `review_core` package instead of copy-pasting Finding/Severity/RuleId/vote_findings/merge_findings into the new LWC reviewer?**
Why: The machinery is language-agnostic — voting, merging, and the Finding/Severity shape
operate on `list[Finding]` regardless of whether findings came from Apex or LWC rules.
Copy-pasting means every future fix (like the nested-parens LOOP_OPEN bug) must be applied
twice and can silently drift. `RuleId` stays a SINGLE shared enum (not per-language) so the
synthesizer never reconciles two vocabularies, and `merge_findings` takes a `regex_owned`
SET AS A PARAMETER now instead of importing a hardcoded one — same function, two callers,
each passing its own owned-rules set.
**Principle:** Extract shared machinery when two consumers need *identical* behavior, not
merely similar. What genuinely differs per language (the rules themselves, the LLM prompt)
stays separate — LWC got its own `rules/` and `reasoning/graph.py`; only the plumbing moved
to `review_core`.

**Q: Why does the router group a `.js` file with a sibling `.html` instead of taking the LWC bundle folder as input?**
Why: LWC components are folders (`myComponent/myComponent.js` + `.html` + meta), but CI/PR
tooling hands you a flat list of changed file *paths*, not folders. Routing by "does a `.html`
with the same stem sit next to this `.js`" works from either a single path or a folder walk,
and degrades gracefully — a JS file with no HTML sibling still gets JS-only checks
(`manual_dom_manipulation` just finds nothing, since it scans the template).
**Principle:** Design the router around the shape of input you actually receive (changed-file
paths from a PR diff), not the architecturally "cleaner" shape (a bundle folder) that's harder
to get from the calling context.

**Q: Why keep the regex layer for LWC when the rules could be LLM-only?**
Why: The free deterministic gate (`eval/runner.py`) must never call an LLM — that's the whole
CI-cost model. LLM-only rules mean no free gate for LWC, and every commit costs money to
verify. Three of the five LWC patterns (`innerHTML =`, `lwc:dom="manual"`, apex-name-called-
in-loop) are syntactically certain — same category as `soql_in_loop` — so regex nails them at
100% recall, free. The two shakier ones (imperative-no-catch, wire-no-error) fired on ~36% of
real ASCENT components — a signal to *measure precision in the eval*, not to abandon regex.
**Principle:** Keep the free deterministic floor for anything syntactically decidable; reserve
the paid LLM layer for genuine judgment calls. Measure the noisy rules; don't drop the layer.

---

## 13. Measuring the LWC reviewer: a perfect score that measured nothing

**Q: The 5 LWC golden cases all scored F1=1.00, spread=0.00 in the paid LLM eval. Why is that NOT good news?**
Why: All 5 LWC rules are `REGEX_OWNED` — the regex layer catches them deterministically, then
`merge_findings` drops the LLM's claims on those same rules. So the LLM contributed *nothing* to
those scores (that's what spread=0.00 tells you — zero run-to-run variance because no LLM output
survived the merge). The paid run just re-confirmed the regex layer, which the FREE `runner.py`
already validates. Money spent, no new information about the thing that costs money (the LLM).
**Principle:** A green metric is only meaningful if the test actually exercises the component you
think you're measuring. Ask "what would have to break for this number to move?" — if the answer
doesn't include the component under test, the metric is blind to it.

**Q: A synthetic bad-example scoring 1.00 doesn't answer the real question. What's missing?**
Why: Every LWC golden case is a *positive* ("this code SHOULD trigger rule X"). None is a
*negative* ("this clean code should stay silent"). Positives measure recall; only negatives
measure **precision** — the false-positive rate. That matters because on 754 real ASCENT
components, `imperative_apex_no_error_handling` and `missing_wire_error_handler` each fired on
~36% — possible mass false-positives that a should-detect golden case can't catch. You can't
measure "does it over-flag?" with examples that are supposed to flag.
**Principle:** A golden set of only positive cases measures recall and hides precision. Add
negative/clean cases (expected findings = empty) to measure the false-positive rate — especially
for rules that fire suspiciously often on real code.

**Q: Two Apex cases FAILed with spread=0.00 and F1=0.67. Bug or not?**
Why: The spread=0.00 + low-score signature means *deterministic* underperformance, not LLM noise.
`review()` consistently returns MORE findings than the golden `expected_rules` lists (regex floor
+ LLM reasoning extras), so precision drops even though nothing is "wrong." Contrast `hardcoded_id`
(F1≈0.58, spread 0.17) — that spread IS genuine LLM wobble. The variance signature tells you where
to look before you touch anything.
**Principle:** Low spread + low score = deterministic (bug OR too-narrow expected set). High spread
= LLM noise. Read the variance signature to route the diagnosis before changing code.

---

## 14. Closing the LWC-LLM blind spot with LLM-only golden cases

**Q: The LWC reviewer's LLM layer had zero eval coverage. How do you build a case that actually tests it?**
Why: Every existing LWC golden case expected a `REGEX_OWNED` rule → the regex layer caught it →
`merge_findings` dropped the LLM's version → the LLM's output never reached the score. The fix is
a case whose expected rule is one the LWC regex layer does NOT own (`exception_risk`,
`high_complexity`, `duplicate_method`). Then the finding can *only* come from the LLM, so the
score moves if and only if the LLM works. Build each case regex-clean by construction (no
innerHTML, no bare wire, no apex-in-loop) and verify with `run_all_rules(js, html) == []` before
trusting it.
**Principle:** To test a specific layer, construct an input only that layer can respond to. If any
other layer can produce the expected output, the case doesn't isolate what you think it does.

**Q: First measurement — two rules at F1=1.00/spread=0, one at F1=0.50/spread=1.00. What does that tell you, immediately?**
Why: `high_complexity` and `duplicate_method` are mechanical (count nesting; compare two bodies)
→ the LLM does them reliably. `exception_risk` (is `data.records[0].Name` a null-risk or normal
LWC?) is a borderline judgment → the model flickers, caught it one run, missed the next. spread=1.00
is the maximum-noise signature — same shape as Apex's wobbly `hardcoded_id`. The variance sorted the
three rules into "trust it" vs "don't" on the very first run.
**Principle:** Spread ranks your rules by trustworthiness for free. Mechanical judgments are stable;
genuinely ambiguous ones flicker — and the flicker is data, not a bug to hide. Keep the noisy case
in the advisory eval (never the CI gate) as living documentation of where the LLM is unreliable.

---

## 15. When the fix is deletion: retiring a regex rule to the LLM

**Q: A regex rule fired on 36% of real components and the sampled hits were ~all false positives. The instinct is to make the regex smarter. Why was the right move to delete it instead?**
Why: The rule asked "does this promise chain handle its errors?" — which requires knowing where
the chain *ends* (balanced parens/braces). Regex can't count balanced delimiters (same wall as the
LOOP_OPEN nested-parens lesson). Every heuristic patch — wider window, neighbor exclusion — is a
worse approximation of a parser, adding code to stay wrong. The project already has a layer that
reasons over whole structures: the LLM. So the rule doesn't need a better regex; it needs a
different layer. Deleting it removed ~78 lines and the entire false-positive source at once.
**Principle:** When a deterministic rule keeps failing because the problem is fundamentally beyond
what that layer can decide, the fix is to move it to the right layer, not to harden the wrong one.
Deletion that relocates responsibility is a feature, not a retreat.

**Q: How did you know it was false-positive noise and not just a strict-but-correct rule?**
Why: You can't tell from the count (273 could be a genuinely bad codebase). You have to *read the
hits*. One sampled file had a perfectly valid `.then().catch()` — the `.catch` just sat past the
window. That single confirmed false positive, plus a second from neighbor-contamination, was enough
to condemn the heuristic — because both failures were structural (every long `.then` body, every
adjacent call), not incidental.
**Principle:** A firing rate is not a precision measurement. Read real hits before trusting — or
retiring — a rule. Structural false positives (a whole class of correct code) justify removal;
incidental ones justify tuning.

---

## 16. Whack-a-mole is a layer signal

**Q: The wire rule's false positives dropped 242→105 with an adapter allowlist, then the remaining hits revealed *two more* error-less adapters to exempt. Why stop patching and retire the rule instead?**
Why: Each fix surfaced the next tier of exemptions (`CurrentPageReference` → then `IsConsoleNavigation`,
`EnclosingTabId` → then what next?). An allowlist that never converges means the rule is encoding a
judgment ("does this wire adapter have a meaningful error path?") that isn't syntactic — it depends on
knowing each adapter's semantics, which is exactly what a regex can't know and an LLM can. Same shape as
the imperative rule: the moment the fix is "add more special cases forever," you're in the wrong layer.
Retiring it left the regex layer with only the 3 rules that ARE syntactically certain
(`unsafe_inner_html`, `manual_dom_manipulation`, `apex_call_in_loop`) — the exact split predicted when
these rules were first built ("three solid, two shaky as regex").
**Principle:** Whack-a-mole — every fix spawning the next special case — is diagnostic, not just annoying.
It means the rule needs knowledge the layer doesn't have. Stop patching; move it to the layer that can
reason. Converging exemptions justify an allowlist; diverging ones justify relocation.

---

## 17. The cross-language finding: derive, don't merge

**Q: The cross-language step "passes both reviewers' output in" — isn't that just merge with two inputs?**
Why: No — and the difference decides the design. `merge_findings` *selects* from findings that already
exist (keep/drop on `(rule, line)`), all about ONE file's two layers. The cross-language step *derives*
a finding that existed in NEITHER input, from the *relationship* between two different files: an LWC
imports `@salesforce/apex/AccountController.x`, the Apex review flagged `AccountController.cls` with
`missing_crud_fls` → emit `cross_language_security_risk` on the component. Three distinct verbs, three
functions: `merge` selects (per file, two layers), `synthesize` consolidates (across files), `correlate`
derives (across the seam). Keeping them separate meant the feature was a pure ADDITION — `synthesize`
and both reviewers didn't change at all.
**Principle:** Name the verb before you name the function. Select, consolidate, and derive are different
operations; collapsing them into one "merge" hides the one that carries the product value.

**Q: Why is this security correlation pure code, when the plan called it the "LLM synthesizer"?**
Why: The v1 signal — "does the called controller carry a security finding?" — is a set-membership check
(match the imported controller name against Apex results that have a security rule). One right answer →
code, per the thesis. Free, deterministic, CI-gateable. The LLM only earns its cost on subtler seams
(data-flow: unsanitized LWC input reaching a SOQL string) — a v2 concern. The valuable part wasn't the
LLM; it was noticing the *relationship* is a first-class thing to check.
**Principle:** "Cross-language" doesn't automatically mean "needs the LLM." Check whether the correlation
is objective first — the cheapest layer that can answer correctly wins, same as everywhere.

---

## 18. Sounds-hard vs is-hard: the real regex-or-LLM test

**Q: The cross-language security check spans two files and sounds fancier than the wire rule — yet it stayed pure code while the wire rule was retired to the LLM. What actually decides it?**
Why: Not "cross-file", not "complex-sounding". The real axis is **bounded-and-decidable vs
unbounded-judgment**. The security check asks "is the called controller in the set of controllers
that have a security finding?" — a set-membership test, one right answer, no growing list of
exceptions. The wire/imperative rules asked "is this adequately handled?" — unbounded: every promise
shape, every error-less adapter is a new special case, so fixes multiply forever (whack-a-mole /
non-convergence). A question that *sounds* hard can be a lookup; a question that *sounds* simple can
hide infinite situations.
**Principle:** Decide the layer by the SHAPE of the question, not its surface complexity. Would two
experts always agree on the answer from fixed inputs? → bounded → code. Does it need reading and
judgment over open-ended situations? → unbounded → LLM. "Cross-file" and "sounds advanced" are
distractions; bounded-vs-unbounded is the cut.

---

## 19. cross_reason: the LLM that reads across the seam — and the true-negative scoring hole

**Q: The cross-language SECURITY check was pure code (§18, bounded set-membership). So why is the cross-language INJECTION check an LLM node with 3× voting?**
Why: Same two files, different question shape. Security asked "does the controller have a security
finding?" — a lookup, bounded, one answer. Injection asks "does *this* untrusted LWC input reach an
*unsafe* dynamic query, and is it actually unsafe (bind var / escapeSingleQuotes / static SELECT =
safe)?" — that's data-flow tracing across a language boundary plus a judgment call on whether the sink
is sanitized. Unbounded → LLM. It's the §18 test applied one level deeper: *cross-language* didn't
decide the layer; *bounded-vs-unbounded* did, again. So `cross_reason` builds an (LWC, Apex-it-calls)
pair, runs the model 3× and keeps findings that clear VOTE_THRESHOLD=2 — the same self-consistency
pattern as graph.py, because a security verdict that flickers 1/3 is noise, not signal.
**Principle:** "Cross-file" is never the deciding attribute. Ask the question's shape every time, at
every layer — the same seam can carry both a lookup (code) and a judgment (LLM).

**Q: The clean twin — an LWC feeding an Apex that *binds* the input — scored F1=0.00 even though the model correctly flagged nothing. Why, and what did that expose?**
Why: The case's `expected_rules=[]`. The old `score` computed precision `tp/(tp+fp)` = `0/0` → 0.0 by
convention. So a **correct true negative and a false positive both score 0.00** — F1 can't tell them
apart when nothing is expected. The negative cases (clean twins) are the whole point of a
false-positive guard, and the scorer was blind to them. Fix: guard empty-expected at the top — found
nothing → precision/recall/F1 = 1.0 (rewarded true negative); found something → 0.0 (real false
positive). Same fix runner.py already had; llm_eval.py's `score` never got it.
**Principle:** A metric that can't distinguish "correctly silent" from "wrongly loud" makes your
negative tests meaningless. When expected is empty, absence *is* the correct answer — score it as a
win, or the clean twin proves nothing.

---

## 20. The clean twin earns its keep: value-side vs query-side concatenation

**Q: The integration test's positive case (concatenated SOQL) passed first try. The NEGATIVE case — an LWC feeding an Apex that binds the input — failed, flagging injection. Was the test wrong?**
Why: No — the test was right, the *model* was wrong, and the negative case is what caught it. The
"safe" Apex was `String pattern = '%' + term + '%'; ... WHERE Name LIKE :pattern`. That `+ term +`
concatenation builds a **value**, which is then **bound** — the user input never enters the query
string, so it's injection-proof (textbook-safe Apex). But the model saw `+ term +` and pattern-matched
"concatenation = injection." The prompt said "bind variables are safe" but never distinguished
**value-side** concatenation (safe: build a value, bind it) from **query-side** concatenation (unsafe:
build the query text passed to `Database.query()`). One line added to the prompt to draw that line, and
the false positive vanished across every re-run.
**Principle:** Negative/clean-twin tests aren't padding — they're how you find the false-positive
engine. A detector that only has positive cases will happily over-fire and you'll never know. The clean
twin failing is the test *working*: it localized a real gap in the model's reasoning that a positive-only
suite is structurally blind to.

**Corollary — probabilistic asserts are inherently flaky.** `assert findings == []` on an LLM node can
wobble 1-in-N even with a good prompt. Binary pass/fail belongs where the value is *measured over runs*
(the eval's FP-rate on the clean twin), not a single-shot integration assert. Fix the prompt so it's
stable, but don't pretend a probabilistic node is deterministic.

---

## 21. The synthesizer: identity before dedup, and group ≠ drop

**Q: `synthesize` was supposed to consolidate findings across files. Why did fixing it start with the _correlate/cross_reason_ output, not with `synthesize` itself?**
Why: You can't dedup until every finding has a unique, honest identity — and the cross findings didn't. `correlate` bucketed every cross-language finding under one synthetic filename `"(cross-language)"` with a placeholder `line=1`. The dedup key `(filename, rule, line)` then collided: two *different* insecure controllers produced the identical key, so dedup would silently drop a real security flag. The synthetic address was a stand-in, not a real coordinate, so it stopped being unique. Fix the identity first: give each cross finding the **controller name** in its filename (`"(cross-language) · AccountController"`), so the coordinate discriminates again. Only then is dedup safe.
**Principle:** Deduplication is only as trustworthy as the identity you dedup on. A placeholder key (synthetic filename, `line=1`) looks like an address but isn't one — collapse on it and you delete signal. Establish real identity before you collapse anything.

**Q: Two different LWCs call the same insecure controller. One finding or two?**
Why: One. The fix lives in the *controller* (add CRUD/FLS, or parameterize the query) — fix it once and every caller goes clean. The callers didn't each introduce a bug; they're each exposed to the same one. So the **controller (and its specific vulnerable line) is the unit of a finding**, and the callers are context. Two callers of one flaw → same key → collapse. Two *different* flaws in one controller → different lines → stay separate (the key already handles that).
**Principle:** The unit of a finding is the thing you fix, not the place you noticed it. Count bugs by remediation, not by observation site.

**Q: When two findings collapse, why merge their messages instead of just keeping one?**
Why: Blind dedup *drops*; a synthesizer must *group* — collapse the identity but **union the context**. Keeping only the first finding loses "acctList.js also calls this." The action is the same (one controller fix), so it's one finding — but the caller list is information, so it's folded into the surviving message (idempotent append, guarded against re-run bloat). Full structured caller-merge (parsed names, not appended prose) waits for a `subject`/caller field on `Finding` — deferred until the linking/rollup phase actually needs it across the shared model.
**Principle:** Group, don't drop. Collapsing duplicates should preserve every distinct piece of context the duplicates carried, even when the remediation is singular.

**Corollary — a clean file is still a result.** Rebuilding `synthesize` from findings alone dropped files with zero findings ("Foo.cls: no issues" vanished). Seed the output with every input filename first, then fill findings. Absence of findings is itself a reportable outcome.

<!-- Append new entries below as we go. Keep it concept + why, skip transient debugging. -->
