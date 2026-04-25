# MNEMOS — Sequence Test Results + Adversarial Trace

**Test-execution log spanning v0.21 phase-1 sequences, v0.22–v0.25 build phases, and Phase 2 / Phase 3 adversarial runs.**

*This document is the test-execution view. `failure_modes.md` is the source of truth for FM definitions; where the two files overlap, `failure_modes.md` wins on wording.*

*Numbering convention: FM-122 through FM-146 and FM-158 through FM-162 are permanent gaps — numbering convenience, not failure modes to discover. Next open number after the v0.25 work: FM-173.*

---

## Implementation Bugs Found During Testing (not FM candidates — code bugs)

### Bug A — Namespace mismatch in search (fixed)
`_hard_write_preference()` and `_promote_synthesizer_facts_to_graph()` in `save_session()` were writing to hardcoded `ns="personal"`. The test called `ask()` without a namespace, defaulting to `"default"`. The belief existed in the graph but `search(namespace="personal")` couldn't find it. Fix: track `_last_namespace` in `ask()` and use it everywhere.

### Bug B — Synthesizer overwrites explicit correction (fixed)
Sequence: `like → hate → like → "No I do NOT like prawns"`. The correction fired correctly, wrote `dislike` at 0.85 confidence. Then `_promote_synthesizer_facts_to_graph()` ran, found `"User likes prawns"` still in `synthesizer._facts` from the previous write, and upserted it back to `like`. Fix: promotion skips any trait where a high-confidence belief (≥0.80) already exists. Explicit corrections always win over synthesizer inference.

---

## Sequence Results

### Category: Context-Heavy

| Sequence | Input | Captured | Graph | Query | Result |
|----------|-------|---------|-------|-------|--------|
| coffee_basic_context | "I don't like coffee" | None — pattern not registered | empty | — | FM-147 |
| coffee_basic_context | "I like coffee in the morning" | None — pattern not registered | empty | — | FM-147 |
| prawns_with_context | "I like prawns when my wife cooks them" | ('prawns','like') — context destructively collapsed | general=like | — | FM-151 |
| work_stress_context | "I like working late" | None — pattern not registered | empty | — | FM-147 |

**Finding:** The ingestion layer (both `_capture_immediate` and `_detect_preference_correction`) only knows about prawns. Coffee, sushi, working late — anything outside the hardcoded pattern list — is invisible (FM-147). Separately, contextual statements like "I like prawns when my wife cooks them" — where the topic *is* in the pattern list but the conditional qualifier isn't — match the polarity word, capture the like, and destructively strip the conditional. The user's statement was true *only* when the wife cooked; the stored belief drops that condition entirely (FM-151).

---

### Category: Temporal Noise

| Sequence | Input | Result |
|----------|-------|--------|
| temporal_used_to | "I hate prawns" → "I used to like prawns" | PASS — temporal blocked |
| temporal_previously | "I like coffee" → "Previously I hated coffee" | PASS — temporal blocked |
| temporal_correction_after_past | "I used to like prawns" → "I hate prawns" | PASS — real correction fires |

**Finding:** Fix 4 (temporal guard) works correctly across all tested forms: "used to", "previously", "before I", "earlier". No false blocks on real corrections.

---

### Category: Mixed / Conditional

| Sequence | Input | Result |
|----------|-------|--------|
| conditional_but | "I hate prawns but my wife loves them" | PASS — user's dislike captured, wife's preference noted as relational |
| partial_preference | "I am not sure if I like prawns" | ⚠️ PARTIAL — fires as 'like' correction (pattern matches "like prawns" in the phrase) |
| negation_forms | "prawns are not my thing" / "not a fan of prawns" | PASS — no capture (correct — these are not in patterns) |
| contradiction_sequence | like → "Actually I hate prawns" | PASS — latest wins |
| overwrite_sequence | like → hate → like → "No I do NOT like prawns" | PASS — latest wins |
| multi_belief | hate prawns + love sushi + dislike weekends | PASS — no cross-contamination |
| context_fragmentation | "morning" vs "early morning" | FM-148 confirmed — treated as separate contexts |
| sparse_graph | query empty graph | PASS — returns NO_BELIEF correctly |

---

## Failure Mode Catalog

### FM-147 — Missing Context Capture
**Status:** CONFIRMED. Expected by Commander V.

**Trigger:** "I like coffee when I am working late" / "I like coffee in the morning"

**System behavior:** `_detect_preference_correction` and `_capture_immediate` only cover prawns. No other domain is registered. "Coffee", "sushi", "working late", and all contextual qualifiers ("in the morning", "when stressed") are invisible to the ingestion layer.

**Why it fails:**
- Pattern list in `_capture_immediate` hardcodes prawns-specific regex
- Pattern list in `PREF_CORRECTION_PATTERNS` hardcodes prawns-specific regex
- Context embedded in sentence ("in the morning") is never extracted — the full sentence goes to `_synthesize()` but no pattern maps "I like X in context Y" to a structured `(trait, value, context)` belief

**What breaks:** Any preference outside prawns is never written to the graph. Any contextual preference ("I like coffee in the morning") is either missed entirely or written as an unconditional general belief, stripping the context.

**Scope:** This is not a regression. The pattern lists were always prawns-only. v0.21 made the gap visible by making the system honest about what it doesn't know.

**Fix direction (v0.22):** The ingestion layer needs to become domain-generic. Either: (a) an LLM extraction call that maps any preference statement to `(topic, value, context)`, or (b) a configurable pattern registry that can be extended without code changes. Option (a) is the correct path — it's what L3 was always meant to be.

---

### FM-148 — Context Fragmentation
**Status:** CONFIRMED. Expected by Commander V.

**Trigger:**
- "I like coffee in the morning" → stored as `context="morning"`
- "I like coffee in the early morning" → stored as `context="early morning"`
- Query with `context="morning"` finds the first but not the second

**System behavior:** Exact string matching means "morning" and "early morning" are different contexts with no relationship. The system cannot infer that "early morning" is a subset of "morning".

**Why it fails:** Context is a string. Equality is exact. There is no context hierarchy, no partial match, no generalization.

**Scope:** This is correct v0.21 behavior — Commander V explicitly said "exact match only, no substring, no scoring changes." The fragmentation is expected and acceptable until v0.22.

**Fix direction (v0.22):** Context normalization layer — either a canonical vocabulary ("morning" covers all morning variants) or a simple synonym map before storage.

---

### FM-149 — Sparse Graph (Expected, Not a Bug)
**Status:** CONFIRMED AS EXPECTED BEHAVIOR.

**Trigger:** Query against empty graph or query for unregistered topic.

**System behavior:** Returns `NO_BELIEF`. Correct. The system is now honest about what it doesn't know.

**This is not a failure.** Commander V predicted this: "You will see 'no belief found' a lot more. Good. That's the next layer."

---

### FM-150 — Partial Negation Capture
**Status:** DETECTED (minor).

**Trigger:** "I am not sure if I like prawns"

**System behavior:** `_detect_preference_correction` fires and returns `('prawns', 'like')`. The phrase "if I like prawns" contains "like prawns" which matches the like pattern. The hedging ("not sure if") is ignored.

**Impact:** Low. The hedging case is genuinely ambiguous — the user is not asserting a preference. The system treating it as a weak like-statement is wrong but not catastrophically wrong.

**Fix direction:** Add an uncertainty guard alongside the temporal guard: phrases like "not sure", "don't know", "maybe", "might" before a preference statement should block capture. Simple regex addition to `_is_declarative()` or a new `_is_uncertain()` gate.

---

### FM-151 — Context Collapse on Conditional
**Status:** CONFIRMED.

**Trigger:** "I like prawns when my wife cooks them" — the pattern matcher captures the like, strips the conditional, stores as unconditional.

**System behavior:** Belief stored as `prawns_preference=like, context=general`. Should be `context=wife_cooks`. The conditional that made the user's statement true is destroyed at ingestion.

**Why it fails:** Pattern-based ingestion has no representation for "when X" conditionals. The patterns matched the polarity word and the topic word; everything between or after was discarded.

**Fix:** v0.22 BeliefExtractor Gate 5 (LLM extraction). The LLM is responsible for identifying conditions and emitting them as the `context` field. Gate 4 normalizes ("when my wife cooks" → "wife_cooks"). Gates 6–10 validate the structured output.

---

### FM-152 — Multi-Context Collapse
**Status:** CONFIRMED.

**Trigger:** "I like coffee in morning and hate it at night" — must produce two beliefs with opposite polarities.

**System behavior:** v0.21 produced one belief or none, depending on which polarity word the pattern matcher found first. The opposing-polarity second clause was lost.

**Why it fails:** No clause splitting. The full sentence was treated as a single match target.

**Fix:** v0.22 controlled clause splitting. Split rules: polarity change ("but hate", "and hate" after a like), or context change with a new predicate. Does NOT split on plain "and" with shared predicate ("I like coffee and tea" stays as one clause). Each clause is then independently processed through Gates 1–10.

---

## Summary

### Phase 1 — v0.21 sequence tests

| Category | Sequences | Pass | Fail | Notes |
|----------|-----------|------|------|-------|
| Context-heavy | 4 | 0 | 4 | FM-147, FM-151 |
| Temporal noise | 3 | 3 | 0 | All temporal guards working |
| Mixed/conditional | 8 | 7 | 1 | FM-150 minor |
| **Phase 1 total** | **15** | **10** | **5** | FM-147, FM-148, FM-150, FM-151, FM-152 |

### Phase 2 — v0.22 build adversarial (A-series)

| Outcome | Inputs | Notes |
|---------|--------|-------|
| Pass | A3, A7, A8, A11 | Gate 7 repair verified, asymmetric context distribution clean |
| Drove fix in v0.24 | A2, A4, A9 (FM-160/163), A12 (FM-161/165) | Cross-clause negation, retrieval substring |
| Deferred | A5 (FM-159), A6 (FM-162), A10 (semantic ambiguity) | Representation work, canonicalization, English ambiguity |
| Refusal correct | A1 | Bare "not when stressed" has no determinable target |

### Phase 3 — v0.24 adversarial pressure (B-series)

| Outcome | Inputs | Notes |
|---------|--------|-------|
| Drove fix in v0.25 | B7 (FM-170) | Highest-severity finding |
| Confirmed deferred | B1, B2 (FM-166), B12 (FM-159), B11 (FM-172) | Held per priority order |
| New failure surfaced | B9 (FM-169) | Normalization shadowing — next priority |
| Boundary property confirmed | B4, B10 (SP-1, SP-2) | LLM coverage limits |
| Latent / accidental | B8 (FM-168), B6 (FM-167-adjacent) | Held with awareness |

### Active FM status

**Active critical FMs: none. Next open number: FM-173+.**

| Status | Count | FMs |
|--------|------:|-----|
| Confirmed and fixed | 12 | FM-147, 150, 151, 152, 153, 154, 155, 156, 157, 160/163, 161/165, 170 |
| Confirmed and deferred | 7 | FM-148, 159, 162, 166, 169, 171, 172 |
| Hypothesized | 4 | FM-158, 164, 167, 168 |
| Confirmed as expected behavior | 1 | FM-149 |
| Structural properties | 2 | SP-1, SP-2 |

### Implementation bugs (separate from FMs)

**Two implementation bugs found and fixed during v0.21 sequence testing.** Both were namespace/confidence enforcement issues, not design failures. Documented above.

### System state after v0.25

- Graph integrity: clean
- Temporal guard: working
- Context retrieval: token-set equality (FM-165)
- Write authority: single path enforced
- Synthesizer authority: subordinated to graph (high-confidence beliefs protected)
- Ingestion: domain-generic via BeliefExtractor (FM-147 closed)
- Negation: per-clause + sentence-scope (FM-160/163 closed for extrapolating-LLM case)
- Trait repair: simple + canonical compound (FM-156, FM-170 closed)
- Engine sentinel: `context=None` enforced (FM-157)
- Open priorities (Commander V order): FM-169, then FM-166, then FM-171/FM-172/FM-167/FM-168, SP-1/SP-2 held

---

## Phase 2 — v0.22 Build Adversarial Sequences (A-series)

**12 inputs. Synthetic test sentences targeting context boundaries, trait drift, restriction enforcement, and clause splitting. Run during the v0.22 build phase against the BeliefExtractor 8-gate pipeline.**

LLM output simulated where API was unavailable. For inputs where LLM behavior is genuinely ambiguous (A2, A9), both faithful and pessimistic LLM paths were traced.

| ID | Input | Result | FM triggered | Notes |
|----|-------|--------|--------------|-------|
| A1 | "I like coffee in the morning and tea at night, but not when stressed" | Bare "not when stressed" has no negation target; system silently dropped it | FM-160 / FM-164 | Genuine ambiguity — refusal is correct |
| A2 | "I like coffee and tea, but not at night" | Faithful LLM: negation lost (no night belief). Pessimistic LLM: night beliefs stored as `like` (wrong) | FM-160, SP-1, SP-2 | Drove FM-163 fix |
| A3 | "I like coffee in the morning and tea at night, but not tea when stressed" | Per-clause Gate 10 inverted tea@stressed correctly | — | Pass |
| A4 | "I like coffee and tea, but only coffee in the morning, not at night" | Pessimistic LLM: cross-clause negation lost | FM-160 | Drove FM-163 fix |
| A5 | "I like coffee on Monday and on Monday mornings" | Both stored independently; no hierarchy | FM-159 | Deferred per Commander V |
| A6 | "I like coffee when I wake up early" | Context becomes `wake_up_early` (LLM-chosen composite) | FM-162 | Deferred — canonicalization scope |
| A7 | "I like monday meetings" | Gate 7 repaired `monday_meeting_preference` → `meeting_preference + monday` | — | FM-156 fix verified |
| A8 | "I like monday morning meetings" | Gate 7 rejected (3+ words) | — | FM-156 strict reject correct |
| A9 | "I like coffee in the morning and tea at night but not on weekends" | Same pattern as A2/A4 — pessimistic LLM produces wrong polarity for weekend | FM-160 | Drove FM-163 fix |
| A10 | "I like coffee and tea in the morning and at night" | LLM produced cross-product (4 beliefs) — semantic question, not a bug | — | Ambiguous English |
| A11 | "I like coffee in the morning and tea with friends" | Asymmetric contexts distributed correctly | — | Pass |
| A12 | "I like coffee at night and at midnight" | Ingestion correct. Retrieval would falsely match `night` to `midnight` via substring | FM-161 / FM-165 | Drove FM-165 fix |

**Phase 2 outcome:** Identified the core failure pattern — clause splitting separates "but not at X" negations from their target clauses; per-clause Gate 10 cannot invert what isn't in its scope. Identified retrieval substring asymmetry — Gate 9 ingestion was token-exact since v0.23, but `matches_context()` was still substring.

**v0.24 fixes from Phase 2:**
- Sentence-scope Gate 10 (`gate_negation_enforcement_sentence`) added as second pass after clause loop. Strict invariants: only flips beliefs that already exist; never creates; never infers.
- `Belief.matches_context()` and `KnowledgeGraph.search()` phase-1 match converted to token-set equality. `None` is the sole wildcard.

After v0.24, A2/A4/A9 pessimistic-LLM paths produce correct polarity. A12 retrieval collision closed.

---

## v0.22 → v0.25 Build Phase Failure Modes

The adversarial build phase between Phase 1 (v0.21 sequences) and Phase 3 surfaced and addressed a series of failure modes through Commander V review and adversarial testing. Definitions are in `failure_modes.md`; the test-execution context is summarized here.

| FM | Phase | Verified by | Fix in version | Status |
|----|-------|-------------|----------------|--------|
| FM-153 | Context over-assignment | v0.22 build | v0.22 (Gate 9) + v0.23 token-exact | Fixed |
| FM-154 | Negation inheritance implicit | v0.22 build | v0.22 (Gate 10 per-clause) | Fixed |
| FM-155 | Object resolution too weak | v0.22 build | v0.22 (Gate 7 INVALID_TRAIT_OBJECTS) | Fixed |
| FM-156 | Strict reject vs recoverable trait drift | A7/A8 + Commander V review | v0.23 (Gate 7 simple repair) + v0.25 (Path B) | Fixed |
| FM-157 | "general" pseudo-context in engine | v0.23 build | v0.23 (`context=None` engine-wide) | Fixed |
| FM-158 | Gate order hypothesis | Commander V review 2 | None — held | Hypothesized |
| FM-159 | Multi-context overlap | A5, B12 | None — deferred | Deferred (representation) |
| FM-160 | Negation scope leak | A1, A2, A4, A9 | v0.24 (sentence-scope Gate 10) | Fixed (extrapolating-LLM case) |
| FM-161 | Retrieval substring matching | A12 | v0.24 (token-set equality) | Fixed |
| FM-162 | LLM soft power over context | A6 | None — deferred | Deferred (canonicalization) |
| FM-163 | Clause-split negation destruction | A2, A4, A9 (same as FM-160) | v0.24 | Fixed |
| FM-164 | Ambiguous negation scope | A1 | None — structural limit | Hypothesized |
| FM-165 | Retrieval substring collision | A12 (same as FM-161) | v0.24 | Fixed |
| FM-170 | Strict reject discards legitimate input | B7 | v0.25 (Gate 7 Path B canonical compound) | Fixed |

---

## Phase 3 — v0.24 Adversarial Pressure (B-series)

**12 inputs. Synthetic test sentences targeting residuals from Phase 2 — dominance heuristic, LLM coverage boundary, trait repair edge cases, normalization edge cases.**

LLM output simulated. For B1 specifically, both pessimistic LLM paths shown to demonstrate FM-166 order-dependence. For B4 and B10, faithful and pessimistic LLM paths shown to demonstrate SP-1 boundary.

| ID | Input | Designed target | Result | FM triggered |
|----|-------|----------------|--------|--------------|
| B1 | "I like coffee in the morning and dislike coffee in the evening, but not at night" | FM-166 dominance | Same input, different LLM output → different graph state | FM-166 |
| B2 | "I dislike coffee in the evening and like coffee in the morning, but not at night" | FM-166 order dependence | Same semantics as B1, reversed clauses → different sentence-pass dominant → different night belief | FM-166 (confirmed cleanly) |
| B3 | "I like coffee in the morning and dislike coffee at night, but not at night" | No-dominant case | Two `coffee@night` beliefs in extracted_beliefs (one per clause); graph dedupes via upsert | FM-166, FM-172 |
| B4 | "I do not like coffee at night" | SP-1 boundary | Faithful LLM: correct. Pessimistic LLM (forgets "not"): no recovery path | SP-1 |
| B5 | "I like coffee in the morning and tea at night, but not coffee at night and not tea in the morning" | Multi-negation mixed scope | Coffee fixed; tea not fixed (all tea contexts in negated set → dominant undetermined) | FM-171 (asymmetric trait correction) |
| B6 | "I like coffee in the morning, but not at night, and I dislike coffee in the evening" | FM-167 clause vs sentence | `split_clauses` produced malformed clause; outcome correct by accident | Clause splitter weakness (FM-167-adjacent) |
| B7 | "I like Monday meetings and Tuesday meetings, but only Monday meetings in the morning" | FM-168 trait repair + restriction | Morning restriction silently DROPPED (Gate 7 strict reject + LLM context set) | FM-170 (highest severity finding) |
| B8 | "I like team meetings and client meetings, but only meetings in the morning" | FM-168 ambiguous restriction token | Saved by accidental pluralization mismatch ("meetings" vs "meeting") | FM-168 (latent, masked) |
| B9 | "I like coffee on Monday and on Monday mornings, but not on Monday mornings" | FM-159 + FM-163 | `normalize_context("monday mornings")` returns `"morning"` (substring shadowing); negated context ≠ stored context; no flip | FM-169 (NEW) |
| B10 | "I like coffee in the morning but not at night" | SP-2 LLM dependency | Path A (LLM extrapolates): correct. Path B (LLM faithful): negation intent lost | SP-1, SP-2 |
| B11 | "I like coffee in the morning, dislike it at night, but not at night" | Cross-context contradiction | 3 beliefs after per-clause; sentence-pass flips one to dislike; result has duplicate at (coffee, night) | FM-172 (duplicate emission) |
| B12 | "I like coffee on Monday but not on Monday morning" | Retrieval brittleness | Ingestion correct. Retrieval: query "Monday afternoon" finds nothing (token-set equality + no hierarchy) | FM-159, FM-165 brittleness made concrete |

**Phase 3 outcome:**

Confirmed pre-named issues:
- **FM-166** order-dependent dominance (B1, B2): same semantic input, different LLM clause order → different sentence-pass dominant → different final state.
- **SP-1** LLM coverage boundary (B4, B10b): system cannot fix what LLM didn't materialize.
- **SP-2** pessimistic-LLM hypothesis (B10): different LLM paths produce different final states for identical input.

New failures surfaced:
- **FM-169** normalization map shadowing (B9): substring iteration in `normalize_context()` collapses compound contexts to atomic ones via key-ordering accident. Specific compounds shadowed by shorter substrings.
- **FM-170** strict reject discards legitimate input (B7): Gate 7's strict-reject path applied too aggressively to legitimate compound input. Highest-severity finding — silent loss of explicit user signal.
- **FM-171** asymmetric trait-level dominance (B5): per-trait dominance computation can't see structural symmetry across traits. Same sentence shape, different correction outcome by trait.
- **FM-172** extracted-list duplicates pre-graph (B3, B11): `extract()` returns non-deduplicated list; graph dedupes at upsert so end-state is correct, but contract is not idempotent.

Latent / accidental:
- **FM-168** pluralization mismatch (B8): collision avoided by accident, not by design. Latent if pluralization ever aligns.
- **FM-167-adjacent** clause splitter weakness (B6): `split_clauses` produces semantically conflated clauses on certain "but not... and..." patterns.

**v0.25 fix from Phase 3:** FM-170 closed via Gate 7 Path B (canonical compound repair). Strict pipeline: normalize drift word and LLM context independently, compose with underscore, validate against `CANONICAL_COMPOUND_CONTEXTS` (derived from `CONTEXT_NORMALIZATIONS.values()`). Composed string is never re-normalized — would reintroduce FM-169 inside the FM-170 fix.

After v0.25, B7 morning restriction is restored. B8 unchanged (no trait drift, Path B does not fire).

**Held per Commander V directive (priority order):**
1. FM-169 — next (normalization shadowing)
2. FM-166 — third (dominance heuristic)
3. FM-171, FM-172, FM-167, FM-168, SP-1, SP-2 — held

---

## Structural Properties

These are not failure modes. They are permanent properties of the current architecture, named explicitly so future work does not mistake them for bugs.

### SP-1 — Determinism Conditional on LLM Coverage

The deterministic gates govern which raw beliefs become final beliefs. They cannot govern which raw beliefs the LLM produces. A negation, restriction, or correction targeting a belief the LLM never materialized cannot be applied by any gate.

This is the boundary between extraction (LLM, stochastic) and validation (gates, deterministic). The system is "deterministic over a stochastic source," not fully deterministic.

Confirmed by Phase 3 B4 (faithful-LLM-forgets-negation) and B10b (no extrapolation).

### SP-2 — Pessimistic-LLM Hypothesis Unvalidated

The FM-163 fix corrects beliefs that the LLM extrapolates with wrong polarity into a separated negation clause. Whether `gpt-5.4-mini` actually produces those extrapolated beliefs in production is unverified.

If the LLM faithfully returns `[]` for isolated "not at X" clauses, the fix has no inputs to correct, and the negation intent is silently lost (SP-1).

A live API run is required to determine which case occurs in practice.

Confirmed by Phase 3 B10 — both LLM paths produce different final states for the identical input.


*Test-execution log. Updated through v0.25 / Phase 3. Live API validation pending — SP-2 will resolve when adversarial sequences are run against the real `gpt-5.4-mini` endpoint rather than simulated LLM output.*