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

<!-- Append new entries below as we go. Keep it concept + why, skip transient debugging. -->
