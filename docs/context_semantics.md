# Context Semantics Specification

**Status:** v1 (governing). Effective from this commit.
**Scope:** MNEMOS L3 ingestion and L2 retrieval — context representation only
**Prerequisite for:** Phase C (FM-169, FM-159, and any successor work touching context)
**Authority:** This document defines the meaning of `context` across the engine. Code that contradicts it is a bug; code that exceeds it requires a Phase C amendment to this document first.

---

## 1. What Context Is

A `context` is **a canonical-form scope qualifier attached to a belief**, drawn from a closed vocabulary, compared to other contexts by exact token-set equality, with `None` as the sole wildcard meaning "unconditional."

Concretely:

- **Type.** `Optional[str]`. Engine state holds either `None` (unconditional) or a non-empty canonical string. The sentinel `None` is the only representation of "applies regardless of context" (FM-157). The string `"general"` is UI-only and never enters engine state.
- **Form.** A canonical string is the output of `normalize_context()` — either an atomic canonical token (`monday`, `morning`) or an underscore-composed pair drawn from `CANONICAL_COMPOUND_CONTEXTS` (`monday_morning`). Composed strings are produced by Gate 7 Path B (FM-170) by independently normalizing each fragment and concatenating with underscore; once composed, they are never re-normalized (FM-169 protection).
- **Comparison.** Two contexts are equal iff their token-set frozensets (split on underscore and whitespace) are identical (FM-165). No substring matching. No subset matching. No hierarchy.
- **Wildcard.** `Belief.matches_context(query)` returns `True` iff `self.context is None` or token-sets are equal. `None` matches every query; no non-None context matches any other non-None context except by equality.

Context is therefore **a label drawn from a finite canonical vocabulary, not a logical condition and not an open-ended set**. The vocabulary is closed by `CONTEXT_NORMALIZATIONS` and `CANONICAL_COMPOUND_CONTEXTS`. The token-set comparison is an implementation choice that enforces equality regardless of internal token order; it does not promote context to a set semantics.

---

## 2. Legal Relationships

The engine expresses exactly two relationships between contexts:

1. **Equality.** `ctx_a == ctx_b` iff frozenset(tokens(a)) == frozenset(tokens(b)).
2. **Universal applicability.** `None` matches everything; everything matches `None`.

**Non-transitivity.** Context matching is not transitive. If `A=None` matches `B=monday`, and `A=None` also matches `C=monday_morning`, this does not imply `B` matches `C`. Universal applicability via `None` is a wildcard rule, not a relational bridge between concrete contexts. Future contributors must not assume mathematical relation properties (transitivity, symmetry beyond equality, hierarchy via shared wildcard) that the matching rule does not provide.

The following relationships are **not legal** in current engine state and must not be inferred by retrieval, ingestion, or any consumer of `Belief.context`:

- **Subset / superset.** `monday` is not a subset of `monday_morning`. They are unequal labels. A belief stored at `monday_morning` does not satisfy a query at `monday`, and vice versa.
- **Hierarchy.** No parent-child relation exists between `monday` and `monday_morning`, between `morning` and `early_morning`, or between any other pair. Compound contexts are atomic strings that happen to contain underscores; the underscore is a composition artifact, not a hierarchy operator. The underscore is representational, not logical.
- **Partial overlap.** Two non-None contexts either match (token-set equality) or do not. There is no "partially applies" state.
- **Temporal scope.** `context` does not encode time bounds, recency, or expiry. CONSTRAINT-tier expiry (L12) is a separate mechanism on the belief, not on its context.
- **Logical composition.** `context` cannot express conjunction beyond what the canonical vocabulary already encodes (`monday_morning` is one canonical atom, not `monday AND morning`). It cannot express disjunction or negation at all.

The set of legal canonical contexts is closed by `CONTEXT_NORMALIZATIONS.values()` and `CANONICAL_COMPOUND_CONTEXTS`. Adding a context value is a vocabulary change, not a runtime operation.

---

## 3. What the Engine Refuses to Model

Each refusal below is permanent under v0.25 semantics. Lifting any of them is a Phase C decision and requires a Section 4 amendment.

- **Refusal: context hierarchy.** No parent/child or general/specific relation. Established by FM-165 (token-set equality) and reinforced by FM-159 (deferred — overlap is a representation problem, not a gate fix). Rationale: a hierarchy without explicit user assertion of generalization invents user intent the system cannot ground.
- **Refusal: partial overlap.** A belief at `monday` and a query at `monday_morning` share the token `monday` but the engine returns no match. Established by FM-165. Rationale: partial overlap requires a confidence-weighted match score the engine deliberately does not compute (Axiom III places uncertainty on the belief, not on the retrieval match).
- **Refusal: temporal scope on context.** `context` does not carry from-to bounds, decay, or recency weighting. Established by Axiom VIII (Bounded Intelligence) and the L12 separation of CONSTRAINT expiry from context. Rationale: time-bounded contexts collapse the trait/context distinction (item 20 of the locked extraction spec).
- **Refusal: logical composition at runtime.** The engine does not interpret `monday AND morning` from `monday_morning`. Composition is vocabulary-level and closed. Established by FM-169 (substring/composition shadowing is a known failure mode being fixed in Phase C, not a feature). Rationale: runtime composition reintroduces normalization paths that have already produced silent failures.
- **Refusal: free-form context strings.** A non-canonical string (`"on tuesdays maybe"`) is normalized to `None` or rejected by Gate 9. Established by FM-157 (engine-wide invariant) and the closed vocabulary in `CONTEXT_NORMALIZATIONS`. Rationale: open vocabulary defeats deterministic equality and reintroduces SP-1 stochasticity into retrieval.
- **Refusal: LLM-decided context semantics.** The LLM extracts candidate context strings (Gate 5); it does not decide whether two contexts are related, hierarchical, or overlapping. Established by SP-1 (deterministic over a stochastic source) and FM-162 (LLM soft power over context — deferred). Rationale: relationship semantics must remain in deterministic code.
- **Refusal: consensus-derived dominance.** Sentence-scope dominant value per trait is determined by first structurally observed non-negated value, not by majority, frequency, confidence aggregation, or semantic consensus across clauses. Two semantically equivalent sentences with different clause order may therefore produce different outcomes (FM-166). Rationale: consensus semantics require the engine to model inter-clause agreement as a first-class representational structure, which v0.25 deliberately does not do.

---

## 4. Phase C Boundary

Phase C may add the following without amending Sections 1–3:

- New canonical entries to `CONTEXT_NORMALIZATIONS` and `CANONICAL_COMPOUND_CONTEXTS` (vocabulary expansion).
- Implementation-level fixes to normalization that preserve the Section 1 definition — specifically, FM-169's longest-key-first or exact-key-only fix.
- New gates or repair paths in `BeliefExtractor` that produce only canonical-vocabulary outputs.
- Test coverage and documentation that verifies the above.

Phase C **may not** do the following without first amending this specification through a Commander V loop:

- Introduce hierarchy, subset, superset, or partial-match relationships between non-None contexts.
- Add temporal qualifiers to `Belief.context`.
- Permit non-canonical strings into engine state.
- Allow the LLM to decide context relationships at retrieval or ingestion time.
- Replace token-set equality with any other comparison (string equality, fuzzy match, embedding similarity, etc.).

FM-159 (multi-context overlap) is the canonical Phase C representation question. Solving it requires either: (a) accepting the current refusal and documenting it as a permanent product limitation, or (b) amending Sections 1–3 to admit a new relationship, with all consequences for retrieval, gate logic, and the FM register made explicit before code changes.

---

## 5. Open Questions

The following are unresolved decisions Phase C must make before implementing the corresponding code. They are not features-in-waiting; they are choice points where two or more answers are coherent and the system has not yet picked one.

- **OQ-1: FM-169 fix shape — staged, not symmetric.** Two options exist: longest-key-first substring normalization (preserves current normalization breadth) or exact-key-only normalization (forces every input through canonical-vocabulary discipline). Substring matching is semantically unstable — it makes representation depend on accidental English morphology rather than explicit canonical declaration. The recommended sequencing is: short-term, longest-key-first as a stabilization patch that removes shadowing corruption while preserving current behavior; long-term, migration to exact-key-only canonicalization as a separate Phase C decision with its own review. The two options are not symmetric and should not be presented as equivalent.
- **OQ-2: FM-159 disposition.** Accept "no match" between `monday` and `monday_morning` as a permanent product behavior (document and close), or admit a hierarchy relationship and amend Section 2? An intermediate option — explicit user-asserted aliasing — is also coherent.
- **OQ-3: Compound vocabulary scope.** `CANONICAL_COMPOUND_CONTEXTS` is currently 6 entries (`after_lunch`, `before_bed`, `monday_morning`, `wife_cooks`, `with_family`, `with_friends`). Should it remain hand-curated (predictable, bounded) or be derived programmatically from the cross-product of base contexts (broader coverage, higher canonicalization risk)?
- **OQ-4: Context-on-correction semantics.** When a user corrects a belief at one context (`"actually I don't like coffee on Mondays"`), does the correction apply to other contexts of the same trait (`coffee + morning`)? Currently no — Gate 10 invariants forbid scope expansion. This is consistent with Section 2 but worth confirming as intentional rather than accidental.
- **OQ-5: Render-layer relationship hints.** UI may want to show "you said you like coffee on Monday" when asked about Monday morning. Is that a render-layer concern (allowed, since Section 3 only constrains engine state) or does it leak relationship semantics that Section 2 forbids? Decision affects L9 Digest behavior.

---

*Every statement in Sections 1–3 is true of the v0.25 codebase. Section 4 is the contract Phase C operates under. Section 5 is the work Phase C must complete before its first non-trivial code change.*

*Revision policy: amendments to Sections 1–4 require Commander V review; amendments to Section 5 (open questions becoming closed decisions) require a paired update to whichever of Sections 1–4 the decision affects.*
