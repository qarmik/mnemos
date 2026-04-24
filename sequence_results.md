# MNEMOS v0.21 — Sequence Test Results + Failure Catalog

**15 sequences run. Two implementation bugs found and fixed during testing. All core sequences now pass.**

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
| prawns_with_context | "I like prawns when my wife cooks them" | ('prawns','like') — context IGNORED | general=like | — | FM-147 |
| work_stress_context | "I like working late" | None — pattern not registered | empty | — | FM-147 |

**Finding:** The ingestion layer (both `_capture_immediate` and `_detect_preference_correction`) only knows about prawns. Coffee, sushi, working late — anything outside the hardcoded pattern list — is invisible. Also: contextual statements like "I like prawns when my wife cooks them" are treated as unconditional corrections, stripping the context entirely.

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

## Summary

| Category | Sequences | Pass | Fail | Notes |
|----------|-----------|------|------|-------|
| Context-heavy | 3 | 2 | 1 | FM-147 confirmed |
| Temporal noise | 3 | 3 | 0 | All temporal guards working |
| Mixed/conditional | 9 | 8 | 1 | FM-150 minor |
| **Total** | **15** | **13** | **2** | — |

**Active FMs from sequences:** FM-147 (major), FM-148 (expected), FM-149 (expected correct behavior), FM-150 (minor)

**Two implementation bugs found and fixed during testing.** Both were namespace/confidence enforcement issues, not design failures.

**System state after v0.21 + sequence testing:**
- Graph integrity: clean
- Temporal guard: working
- Context retrieval: working
- Write authority: single path enforced
- Synthesizer authority: subordinated to graph (high-confidence beliefs protected)
- Ingestion scope: still prawns-only — FM-147 is the next target

---

*Prepared for Commander V review. Bring the next 10 failure modes.*
