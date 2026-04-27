# MNEMOS Architecture Reference

**Version:** mnemos-lite v0.25
**Status:** Operational — graph integrity confirmed, temporal consistency stable, 16 real sessions complete, Phase 2 + Phase 3 adversarial sequences run, BeliefExtractor (L3 ingestion) operational

---

## Design Axioms

Nine axioms. No layer may violate any of them.

| # | Axiom | Rule |
|---|-------|------|
| I | Salience ≠ Truth | Importance scoring governs retrieval priority only — never epistemic status. A highly salient belief is not a more true belief. |
| II | Provenance is Permanent | Every belief traces to its source. Raw episodic records are never destroyed. The audit log is immutable. |
| III | Uncertainty is First-Class | Every belief carries Beta(α,β). The variance of a belief is as important as its mean. Confidence ≠ truth. |
| IV | Trust is Tiered | PREFERENCE: high (user is ground truth). Self-reported facts: medium. External facts: low, require grounding. |
| V | Failures Must Be Loud | Silent failures are architecturally prohibited. Every layer exposes a health signal. |
| VI | Correctness + Speed Coexist | Dual-path architecture: Fast path (<50ms) for responsiveness, Deep path (async) for correctness. Neither sacrifices the other. |
| VII | The System Must Be Legible | L9 Memory Digest renders calibrated language, evidence counts, and an epistemic footer on every call — without exception. |
| VIII | Bounded Intelligence Wins | Non-Adaptive Core + Stability Budget + convergence criterion. The system knows when to stop updating. |
| IX | Remain Permanently Breakable | L15 Adversarial Layer runs continuously. The FM Register is never closed. Belief in completeness is prohibited. |

---

## Objective Hierarchy

Lexicographic — higher objectives satisfied completely before lower ones are considered.

| Priority | Objective | Rule |
|----------|-----------|------|
| 1 — Highest | Safety + Truth | SAFETY / MEDICAL / LEGAL / FACTUAL-immune beliefs always surface. No outcome score or preference may override them. |
| 2 | User Outcome Quality | Maximize L14 Correction-Resistance. The system's own corrections decrease over time as the user grows. |
| 3 | Memory Accuracy | High belief accuracy and retrieval precision. Means to Priority 2, never a primary end. |
| 4 — Lowest | Consistency | Predictable behavior. Never justifies sacrificing accuracy or outcomes. |

---

## The 17 Layers

MNEMOS has 17 layers (L0 through L16). Not all are equally mature in the current prototype. For current production behavior, focus on L0–L4, L9, L12–L15.

### L0 — Fast Path
Real-time belief access. TTL 72 hours. Target: <50ms.

- Volatility scoring on writes
- Consequence Override channel for high-weight signals
- Session initializes from Deep path snapshot

### L1 — Episodic Store
Verbatim write-once records. The ground truth of what was said.

- BM25 + dense vector hybrid search with RRF fusion
- PAWD (Provenance-Adjusted Weight Decay) retrieval penalty
- Hot / warm / cold tiers by recency

### L2 — Knowledge Graph
Beta(α,β) belief nodes with typed edges.

- Bounded Influence Zones (BIZ) — propagation is scoped, not global
- Incremental belief propagation (dirty-node queue)
- Integration quarantine for unverified incoming beliefs
- `remove_by_trait(trait, namespace)` — hard-deletes all beliefs matching a trait before writing a correction. No soft coexistence. Truth replaces prior. (v0.19 / FM-121)
- `upsert_belief(belief)` — enforces one belief per trait per namespace. Updates in place if trait exists, else inserts. (v0.19 / FM-121)

### L3 — Semantic Store / Ingestion Layer
The path from raw user utterance to validated structured belief. Two halves:

**Ingestion (v0.22+, implemented):** `BeliefExtractor` — 10-gate pipeline. LLM extracts structure; system decides truth. See *BeliefExtractor — 10-Gate Pipeline* section below for full specification.

**Async consolidation (design target, not yet implemented):**
- Domain-typed claims graduated from L1 episodic records
- Self-consistency veracity scoring
- Version diffing + drift alerts

**Status:** Ingestion layer implemented (v0.22, hardened through v0.25). Async consolidation remains a design target.

### L4 — Inference Engine
Read-only context assembly. Never writes to the graph.

- Credibility filter: decision relevance × recency, not just similarity
- Conflict objects surfaced explicitly rather than hidden
- Core-first injection: CONSTRAINT and IDENTITY always load first

### L5 — Safety Layer
Anomaly detection and circuit breakers.

- Confirmation anomaly detector (catches sycophantic drift)
- Semantic framing classifier (experiential vs epistemic language)
- Cascade-break firewall

**Status: Partial.**

### L6 — Audit Log
Immutable append-only event log.

- Cryptographically signed records
- Performance events
- All FM Register entries written here

### L7 — Grounding Oracle
External validation. **FACTUAL domain only.**

- Domain-gated: preferences and identity never sent to oracle
- Self-consistency model for preference validation (internal only)

**Status: Design target — not yet implemented in prototype.**

### L8 — Token Budget
Progressive context loading.

| Tier | Budget | Contents |
|------|--------|----------|
| Core | 120T | CONSTRAINT + IDENTITY beliefs |
| Fast | 80T | High-salience recent beliefs |
| Essential | 500T | Relevant retrieved beliefs |
| On-demand | 200T | Causal edges + episodic context |

### L9 — Memory Digest
Human-readable summary. **Epistemic footer on every render, without exception.**

- Confidence-stratified rendering
- Evidence counts shown for every belief
- Calibrated language: "Based on N instances — tentative / moderate / high confidence"
- Degradation disclosure when operating in reduced mode

### L10 — Meta-Memory
Self-evaluation of memory quality. Bounded.

- Epsilon-floor: exploration budget never drops to zero
- Causal gate: all updates require L13 attribution
- Outcome primacy: L14 score gates L10 updates
- RWB (Reflexive Work Budget) hard cap: prevents meta-loop instability

**Status: Partial.**

### L11 — Arbitration Engine
Cross-path conflict resolution.

- 3 strategies with Strategy Diversity Budget (max 70% any single strategy)
- Risk Mode Momentum: escalating exit cost prevents oscillation
- SLAs per conflict type

**Status: Partial.**

### L12 — Non-Adaptive Core
Frozen beliefs. Nothing here updates from interaction.

- **IDENTITY**: permanently frozen per namespace
- **CONSTRAINT**: typed expiry (180 days for medical/safety; never for identity)

### L13 — Causal Attribution
Gates all L10 updates with causal analysis.

- 4 candidate causes evaluated per update
- Confidence-proportional update magnitude
- `observed_weight` vs `validated_weight` — validation requires 2+ distinct contexts

### L14 — Outcome Layer
User outcome as primary optimization target.

- Comfort vs Correction-Resistance tradeoff
- Truth-Preservation Override: 4 immune classes always surface
- System's own correction rate decreases over time as user becomes more independent

### L15 — Adversarial Layer
Permanent internal critic. Structurally isolated.

- Adversarial probes against all stable beliefs
- Convergence Audits every 90 days
- FM Register: append-only, never closed
- Structurally isolated: cannot be silenced by other layers

### L16 — Context Policy
Namespace-scoped objective configurations.

- Maximum 5 namespaces (prevents policy explosion)
- Policy inheritance: child namespaces inherit from parent
- Drift detection at thresholds 0.25 / 0.40 / 0.60

**Status: Partial.**

---

## BeliefExtractor — 10-Gate Pipeline

The L3 ingestion layer. Converts a user utterance into validated structured beliefs.

**Core principle:** LLM extracts structure. System decides truth.

The LLM (currently `gpt-5.4-mini`) is responsible for parsing natural language into `(trait, value, context, confidence)` tuples. Every other decision — what to write, what to reject, how to repair, when to invert polarity — is deterministic. The LLM never decides whether a belief enters the graph.

**Falls back gracefully:** If no API key is available, deterministic gates 1-4 and 6-10 still run; Gate 5 returns empty; the extractor produces no beliefs but emits no errors. Pre-v0.22 pattern-based capture is no longer used.

### Pipeline structure

Sentence
│
├─ Controlled clause splitting
│   (split on polarity change OR context change with new predicate;
│    no split on shared predicate "I like coffee and tea")
│
└─ For each clause:
Gate 1  — Temporal       (block "used to", "previously", "before I")
Gate 2  — Uncertainty    (block "might", "not sure", "maybe")
Gate 3  — Subject        (require explicit "I"; route relational to notes)
Gate 4  — Context normalize (canonical form via CONTEXT_NORMALIZATIONS)
Gate 5  — LLM extraction  (parse to (trait, value, context, confidence))
Gate 6  — Value normalize (map to {like, dislike}; neutral → no write)
Gate 7  — Object/trait validation
Path A: simple repair when LLM context empty
Path B: canonical-compound repair when LLM context set
Gate 8  — Confidence filter (only "explicit" writes)
Gate 9  — Context assignment validation (FM-153 — restrict over-assignment)
Gate 10a — Negation enforcement (per-clause)
After all clauses:
Gate 10b — Negation enforcement (sentence-scope second pass) (FM-163)
→ Validated beliefs flow to graph.upsert_belief()

### Gate-by-gate specification

**Gate 1 — Temporal.** Blocks past-state assertions like "I used to like prawns" — the user is reporting history, not current state. Pass-through overrides: "but now", "these days", "currently". State transitions ("stopped liking X") flip polarity rather than block.

**Gate 2 — Uncertainty.** Blocks hedged statements: "might", "not sure", "maybe", "I think", "I guess". Comparative phrasing ("prefer X over Y") is also blocked. Directional preference with context ("prefer X at \<context\>") is allowed.

**Gate 3 — Subject.** Requires explicit first-person subject. "My wife likes coffee" is routed to a relational note rather than written as a belief. "My wife and I both like coffee" passes (the "I" is explicit).

**Gate 4 — Context normalization.** Maps raw context strings to canonical form via `CONTEXT_NORMALIZATIONS`. Returns `None` for empty / "general" / "none" — `None` is the engine's sole sentinel for "unconditional" (see Belief Data Model section).

**Gate 5 — LLM extraction.** The single point where the LLM acts. Receives one clause, returns a list of `{trait, value, context, confidence}` dicts. Never decides whether to write.

**Gate 6 — Value normalization.** Maps LLM-emitted value strings to `{like, dislike}`. Neutral, unrecognized, or empty values produce no write — absence is more honest than fabrication.

**Gate 7 — Object/trait validation.** Two checks:
- *Pronoun rejection (FM-155):* trait whose entity word is in `INVALID_TRAIT_OBJECTS` is rejected outright.
- *Trait drift handling (FM-156, FM-170):* if a context word leaked into the trait name (e.g., `monday_meeting_preference`), attempt deterministic repair. Two paths:
  - **Path A — LLM context empty:** move drift word into the context field. `monday_meeting_preference + None` → `meeting_preference + monday`.
  - **Path B — LLM context set:** compose canonical compound from independently-normalized parts. `monday_meeting_preference + "morning"` → `meeting_preference + monday_morning` (only if the composed string is in `CANONICAL_COMPOUND_CONTEXTS`). Otherwise reject.

The composed string is **never re-normalized** — that would reintroduce FM-169 substring shadowing inside the FM-170 fix.

**Gate 8 — Confidence filter.** Only `confidence == "explicit"` writes proceed. `"implicit"` (LLM-inferred) is rejected.

**Gate 9 — Context assignment validation (FM-153).** Post-LLM deterministic check. If the clause text contains an explicit restriction marker ("only X", "X only", "but only X"), context is valid only for the explicitly named object. All other objects' contexts are demoted to `None`. Object matching uses token-set intersection (no substring) — "tea" does not match "steak"; "car" does not match "carpet".

**Gate 10a — Negation enforcement, per-clause (FM-154).** Detects "not at/in/during/on/when \<context\>" phrases inside the clause. For any belief whose context matches a negated context, force value to opposite of the trait's dominant (first-encountered, non-negated) value.

**Gate 10b — Negation enforcement, sentence-scope second pass (FM-163).** After all clauses are processed, scan the full sentence for "not at/in/during/on/when \<context\>" phrases. For any existing belief (across all clauses) whose context matches a negated context, flip value to opposite of the trait's non-negated dominant.

**Strict invariants on the sentence-scope pass:**
- Operates only on beliefs that already exist in the extracted set.
- Never creates beliefs.
- Never infers missing targets.
- Never expands scope beyond the negated context set.
- Idempotent with Gate 10a (won't re-flip what was already corrected — guarded by `eb.value == dom` check).

The system models observed structured statements, not logical negation. If the LLM did not produce a belief at the negated context, sentence-scope has nothing to flip; the negation intent is silently lost. This is acknowledged as **SP-1** (see Structural Properties).

### Canonical compound contexts

`CANONICAL_COMPOUND_CONTEXTS` is derived at module load from the values in `CONTEXT_NORMALIZATIONS` that contain underscores. The map is the authority on what compound contexts are recognized; if a Gate 7 Path B composition isn't in the set, the system refuses to fabricate it. Current set: `{after_lunch, before_bed, monday_morning, wife_cooks, with_family, with_friends}`.

### Open / deferred items in the pipeline

| FM | Issue | Status |
|----|-------|--------|
| FM-159 | Multi-context overlap (no hierarchy) | Deferred — representation work |
| FM-162 | LLM soft power over context strings | Deferred — canonicalization scope |
| FM-166 | Order-dependent dominance in sentence-scope | Deferred — heuristic limit |
| FM-169 | Normalization map shadowing | Next priority — substring iteration order |
| FM-171 | Asymmetric trait-level dominance | Deferred — representation |
| FM-172 | Extracted-list duplicates pre-graph | Deferred — masked by upsert dedup |

See `failure_modes.md` for full register.

## Belief Data Model

Structured belief fields (introduced v7, FM-76; updated v0.23 for FM-157).

```python
@dataclass
class Belief:
    trait:             str            # What aspect (e.g. 'response_style', 'prawns_preference')
    value:             str            # Observed value (e.g. 'concise', 'dislike')
    context:           Optional[str]  # When/where it applies — None = unconditional (FM-157)
    exceptions:        List           # Noted exceptions
    content:           str            # Auto-generated label
    domain:            Domain         # See domains below
    namespace:         str            # work / health / personal / research / ...
    alpha:             float          # Beta distribution alpha
    beta_:             float          # Beta distribution beta
    evidence_count:    int            # Total interactions this belief appeared in
    last_confirmed:    float          # Timestamp of last explicit confirmation
    last_contradicted: float          # Timestamp of last contradiction (FM-83 recency override)
    source_text:       str            # Evidence this belief was drawn from (FM-72)
```

`confidence = alpha / (alpha + beta_)`

**Key insight:** `'concise at work'` and `'detailed when learning'` are two non-contradictory beliefs about the same trait. The `context` field is a hard gate in retrieval — not a soft hint.

### `context=None` engine invariant (FM-157)

The string `"general"` is **not** a valid engine-side value for `context`. `None` is the sole sentinel for "this belief is unconditional".

- `"general"` is a UI/display label only. It may appear in rendered output; it never appears in engine state.
- `add_belief()` normalizes legacy `"general"` / `""` strings to `None` at the API boundary.
- `matches_context(query)` returns `True` for any query when `self.context is None` — this is the only wildcard.
- For conditional beliefs (`context` is a string), `matches_context()` requires **token-set equality** with the query (FM-165). Tokenize on underscore and whitespace; require frozenset equality. No substring, no subset, no hierarchy.

This invariant prevents two failure modes:
- Pre-v0.23: `context=None` and `context="general"` were indistinguishable, causing overwrite collisions.
- Pre-v0.24: `matches_context` used substring matching — `"night"` falsely matched `"midnight"`; `"work"` falsely matched `"homework"`.

### Preference hard-write (v0.19 / FM-120 / FM-121)

When a user explicitly corrects a preference ("No, I do NOT like prawns"), `_hard_write_preference()` calls `remove_by_trait()` to delete all prior beliefs for that trait, then `upsert_belief()` to write a single authoritative belief at alpha=5.0, beta_=0.9 (confidence ≈ 0.85). The graph holds exactly one truth. The LLM's conversation history is irrelevant to preference state.

### Belief uniqueness key (v0.21 / FM-121)

`graph.upsert_belief()` enforces uniqueness on `(trait, namespace, context)`. Different contexts for the same trait produce different beliefs — `coffee_preference + morning` and `coffee_preference + evening` coexist. Same `(trait, namespace, context)` updates in place; never duplicates.

## Belief Data Model

Structured belief fields (introduced v7, FM-76).

```python
@dataclass
class Belief:
    trait:             str      # What aspect (e.g. 'response_style', 'prawns_preference')
    value:             str      # Observed value (e.g. 'concise', 'dislike')
    context:           str      # When/where it applies — hard-gated in retrieval (FM-81)
    exceptions:        List     # Noted exceptions
    content:           str      # Auto-generated label
    domain:            Domain   # See domains below
    namespace:         str      # work / health / personal / research / ...
    alpha:             float    # Beta distribution alpha
    beta_:             float    # Beta distribution beta
    evidence_count:    int      # Total interactions this belief appeared in
    last_confirmed:    float    # Timestamp of last explicit confirmation
    last_contradicted: float    # Timestamp of last contradiction (FM-83 recency override)
    source_text:       str      # Evidence this belief was drawn from (FM-72)
```

`confidence = alpha / (alpha + beta_)`

**Key insight:** `'concise at work'` and `'detailed when learning'` are two non-contradictory beliefs about the same trait. The `context` field is a hard gate in retrieval — not a soft hint.

**Preference hard-write (v0.19/FM-120/FM-121):** When a user explicitly corrects a preference ("No, I do NOT like prawns"), `_hard_write_preference()` calls `remove_by_trait()` to delete all prior beliefs for that trait, then `upsert_belief()` to write a single authoritative belief at alpha=5.0, beta_=0.9 (confidence ≈ 0.85). The graph holds exactly one truth. The LLM's conversation history is irrelevant to preference state.

---

## Belief Domains

| Domain | Trust | Truth-Immune | Notes |
|--------|-------|:------------:|-------|
| `FACTUAL` | Low → oracle validates | Yes | External claims require L7 grounding |
| `CONSTRAINT` | High + Anchored | Yes | Allergies, legal, safety. Always surfaces regardless of retrieval score |
| `PREFERENCE` | High — user is ground truth | No | User is absolute authority. Hard-written on explicit correction. Never overridden by outcome score |
| `EVALUATIVE` | Medium — attributed | Only if ext. | Assessments, not facts. Source attribution mandatory |
| `IDENTITY` | User-defined | No | Multi-stable. Never force-merged across namespaces |
| `CAUSAL` | Medium | No | `observed_weight` vs `validated_weight`. Validated only after 2+ distinct contexts with no contradictions |

---

## Key Classes (v0.25)

| Class | FMs Addressed | Responsibility |
|-------|---------------|----------------|
| `MnemosLite` | Orchestrator | `new_session()` / `ask()` / `digest()` / `save_session()` / `_canonicalize_query()` / `_extract_and_write_beliefs()` / `_hard_write_preference()` |
| `BeliefExtractor` | 147, 150–157, 163, 170 | L3 ingestion (v0.22+). 10-gate pipeline. LLM extracts structure; system decides truth. `extract()` / `extract_with_trace()` |
| `Belief` | 76, 67, 83, 84, 157, 165 | Structured belief with Beta(α,β). `context: Optional[str]` (None = unconditional). `matches_context()` uses token-set equality |
| `KnowledgeGraph` | 17, 22, 121, 165 | Beta nodes, BIZ propagation. `add_belief()` / `remove_by_trait()` / `upsert_belief()` / `search()` with token-set context match |
---

## InteractionMemory Priority Stack

The exact order in which `ask()` makes interaction decisions. Higher priority gates bypass everything below.

| Priority | Gate | Condition | Action |
|----------|------|-----------|--------|
| 1 — Absolute | FM-91 Intent Override | `detect_intent_override()` returns `force_reflect` or `force_answer` | Force mode. Bypass everything. |
| 2 | FM-93 Topic Preference | `answer_pref_confidence >= 0.65` on this topic cluster | Suppress re-entry. Answer directly. |
| 3 | FM-87 Forced Re-entry | 7+ direct answers on topic AND prior history AND no cooldown | Attempt one soft reflection. |
| 4 | FM-85/86 Budget | Attempts ≥ 2 AND successes = 0, OR cooldown active, OR resistance ≥ threshold | Block reflection. Answer. |
| 5 | FM-73 Intervention | Urgency keywords, or decision intent ≥ 0.5 | Policy decision. |
| 6 | FM-90 Resistance | `confidence_of_resistance >= 0.65` (requires 2+ signals) | Suppress reflection. |
| 7 — Default | — | Nothing fired | Answer directly. |

---

## Cross-Session Memory Architecture (v0.14+, ingestion updated v0.22+)

```
Session end:
  save_session()
    → SessionSynthesizer._synthesize() [forced flush of turn buffer]
    → PersistentProfile.update_from_session(session_facts, preferences)
        → SEMANTIC_TOPICS dedup: same-topic facts resolve by timestamp, latest wins
        → SLOW_DECAY_PREFIXES: identity-core facts decay at 0.05/session
        → Standard facts: decay at 0.10/session, retire at <0.30 confidence
        → Writes to mnemos_memory/user_profile.json

Session start:
  new_session()
    → profile._load() [fresh disk read — never uses __init__ snapshot]
    → disk_facts injected into synthesizer._facts as "[from prior session, tentative] ..."
    → context_for_session() returns identity-class facts only (preference-class suppressed)
    → Cold-start: persona, workplace, relational facts shown; prawns preference not shown

Per-turn (v0.22+):
  _extract_and_write_beliefs(text)
    → BeliefExtractor.extract(text)
        → Per-clause: Gates 1–10a (temporal, uncertainty, subject, context-norm,
                                    LLM, value-norm, object, confidence,
                                    context-assignment, per-clause negation)
        → Sentence-scope: Gate 10b (cross-clause negation enforcement)
    → For each validated belief: graph.upsert_belief(belief) at conf=0.85
    → Falls back to v0.21 patterns if OpenAI API unavailable

Preference correction:
  _detect_preference_correction(text) [single-fire: only when response_text == ""]
    → _hard_write_preference(topic, value, namespace)
        → graph.remove_by_trait(trait)   [hard delete all prior beliefs for this trait]
        → graph.upsert_belief(new_belief) [one authoritative belief at conf=0.85]
        → synthesizer._facts purged of opposite signal

```

## Version Arc

| Version | Core Question | Key Mechanism |
|---------|---------------|---------------|
| v0.1–v0.7 | What breaks in code? | Full prototype, FM-61 through FM-93 |
| v0.8 | Real-session calibration (sessions 1–3) | FM-94–101: persona routing, topic key, emotion, register |
| v0.9–v0.11 | Social intelligence + identity coherence (sessions 4–7) | FM-102–112: SocialStateTracker, SessionSynthesizer, persona payload |
| v0.12 | Disk persistence live (session 8) | FM-113–115: PersistentProfile, preference conflict history, decay |
| v0.13 | Cold start UX (session 9) | get_cold_start_note(), BELIEF ACTIVATION RULE, EPISTEMIC ATTEMPT RULE |
| v0.14 | FM-116: cross-session read failure | Three-bug fix: _capture_immediate(), forced _synthesize(), fresh disk read |
| v0.15 | FM-117: false positive capture | _is_declarative() gate, SEMANTIC_TOPICS dedup, confidence weighting |
| v0.16 | FM-118: evaluative fact blindness | Relational capture, SLOW_DECAY_PREFIXES, UAI minimum sample fix |
| v0.17 | FM-119: third-person identity bypass | Phrase-level canonicalization, BELIEF_QUERY_PATTERNS extended |
| v0.18 | FM-120: in-session preference decay | Hard-write on correction, proactive surfacing gate |
| v0.19 | FM-121: belief graph corruption | remove_by_trait(), upsert_belief(), single-fire gate |
| v0.20 | PREFERENCE CONFIRMATION RULE | Reaffirmation is not contradiction |
| v0.21 | Sequence test phase | FM-147–152: pattern-list limits exposed, context collapse on conditional, multi-context collapse |
| v0.22 | BeliefExtractor — L3 ingestion live | FM-153–155: 8-gate pipeline (temporal, uncertainty, subject, context-norm, LLM, value-norm, object, confidence). LLM extracts structure; system decides truth |
| v0.23 | Engine invariants + token-exact ingestion | FM-156: Gate 7 simple repair. FM-157: `context=None` engine-wide. Gate 9 token-exact restriction matching |
| v0.24 | Cross-clause negation + retrieval discipline | FM-160/163: sentence-scope Gate 10 second pass. FM-161/165: token-set equality at retrieval (`matches_context`, `graph.search` phase 1) |
| v0.25 | Truth preservation under compound input | FM-170: Gate 7 Path B canonical compound repair (independent normalization, composed underscore, validated against `CANONICAL_COMPOUND_CONTEXTS`). Composed string never re-normalized — would reintroduce FM-169 |

---

## Phase Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| Phase A | Contextual belief system invariants | Done (v0.21) |
| Phase B | L3 ingestion correctness — BeliefExtractor | Done (v0.22 → v0.25) |
| Phase C | Context interpretation — normalization, compatibility, hierarchy | Next. FM-169 (normalization shadowing) is the first concrete fix in this phase. FM-159 (multi-context overlap) is the larger representation question. |
| Phase D | L3 async consolidation, L10 meta-memory | Later |
| Phase E | L7 grounding, L11 arbitration, L16 policy | Later |

The roadmap is sequenced. Phase C cannot start cleanly while Phase B has open critical issues; Phase D representation work depends on Phase C decisions about hierarchy.

---

## Structural Properties

These are not failure modes. They are permanent properties of the current architecture, named explicitly so future work does not mistake them for bugs.

### SP-1 — Determinism Conditional on LLM Coverage

The deterministic gates govern which raw beliefs become final beliefs. They cannot govern which raw beliefs the LLM produces. A negation, restriction, or correction targeting a belief the LLM never materialized cannot be applied by any gate.

This is the boundary between extraction (LLM, stochastic) and validation (gates, deterministic). The system is "deterministic over a stochastic source," not fully deterministic.

### SP-2 — Pessimistic-LLM Hypothesis Unvalidated

The FM-163 (sentence-scope negation) fix corrects beliefs that the LLM extrapolates with wrong polarity into a separated negation clause. Whether `gpt-5.4-mini` actually produces those extrapolated beliefs in production is unverified.

If the LLM faithfully returns no beliefs for isolated "not at X" clauses, the fix has no inputs to correct, and the negation intent is silently lost (SP-1).

A live API run is required to determine which case occurs in practice. This will resolve when adversarial sequences are run against the real API endpoint rather than simulated LLM output.

See `failure_modes.md` for the full register and `sequence_results.md` for the test-execution log demonstrating both SP-1 and SP-2 in Phase 3.