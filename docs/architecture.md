# MNEMOS Architecture Reference

**Version:** mnemos-lite v0.20
**Status:** Operational — graph integrity confirmed, temporal consistency stable, 16 real sessions complete

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

### L3 — Semantic Store
Async consolidation. Beliefs graduate here from episodic records.

- Domain-typed claims
- Self-consistency veracity scoring
- Version diffing + drift alerts

**Status: Design target — not yet implemented in prototype.**

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

## Key Classes (v0.20)

| Class | FMs Addressed | Responsibility |
|-------|---------------|----------------|
| `MnemosLite` | Orchestrator | `new_session()` / `ask()` / `digest()` / `save_session()` / `_canonicalize_query()` / `_detect_preference_correction()` / `_hard_write_preference()` |
| `Belief` | 76, 67, 83, 84 | Structured belief with Beta(α,β). `apply_decay()`, `confidence_qualifier()`, `recency_boost()` |
| `KnowledgeGraph` | 17, 22 | Beta nodes, BIZ propagation. `add_belief()` / `remove_by_trait()` / `upsert_belief()` / `search()` |
| `EpisodicStore` | L1 | Write-once records. BM25 + ChromaDB hybrid with RRF fusion |
| `FastPath` | L0, 24 | TTL 72h in-memory cache. Volatility scoring |
| `PersistentProfile` | 113, 115, 116–121 | Disk-backed cross-session memory. SEMANTIC_TOPICS conflict dedup. Differential decay. Cold-start preference gating |
| `SessionSynthesizer` | 105, 107, 94 | Compressed user model every 5 turns. `_capture_immediate()` / `_is_declarative()` / `_synthesize()` |
| `LongTermBehavior` | 89, 93 | Cross-session behavioral baseline. Per-topic answer/reflect preference |
| `InteractionMemory` | 85–93 | Reflection budget, resistance, re-entry, FM-93 preference gate. `should_reflect()` / `record_exchange()` |
| `SocialStateTracker` | 102–108 | Live adversarial/depth/trust state across turns. `system_notes()` for prompt injection |
| `EmotionIntensityClassifier` | 101 | LOW / MEDIUM / HIGH tiers. `system_note()` per tier |
| `FrustrationTracker` | 98 | Frustration → change approach immediately. `system_note()` |
| `ConversationalRegister` | 100 | Casual register → prose instruction. `is_casual()` / `system_note()` |
| `CalibratedInferencer` | 105 | Probabilistic inference from session context with stated confidence |
| `AutonomyTracker` | 61, 70, 79 | Counterfactual UAI. `natural_r` vs `prompted_r`. Minimum 3 natural interactions before delta penalty applies |
| `ResponseValidator` | 78, 82 | `CONSTRAINT_EXPANSIONS`: shellfish → shrimp/prawn/crab/lobster/... `validate()` |
| `ForgettingPolicy` | 71 | PAWD decay + entropy retire + retrieval penalty |
| `FMRegister` | 14, 50 | Immutable append-only failure mode register. `log()` / `summary()` |

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

## Cross-Session Memory Architecture (v0.14+)

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

Per-turn:
  _capture_immediate(text) [FM-117 gate: declarative statements only, never questions]
    → Immediate facts written to _facts and long_term._session_facts

Preference correction:
  _detect_preference_correction(text) [single-fire: only when response_text == ""]
    → _hard_write_preference(topic, value, namespace)
        → graph.remove_by_trait(trait)   [hard delete all prior beliefs for this trait]
        → graph.upsert_belief(new_belief) [one authoritative belief at conf=0.85]
        → synthesizer._facts purged of opposite signal
```

---

## Version Arc

| Version | Core Question | Key Mechanism |
|---------|---------------|---------------|
| v1 | What to store? | Separation of salience and truth |
| v2 | How to behave? | Fast path + Deep path + BIZ |
| v3 | How to learn? | L10 Meta-Memory, L15 Adversarial |
| v4 | When to stop? | Non-Adaptive Core, L13 Causal |
| v5 | What don't I know? | FM Register open forever |
| v6 | How to govern? | L16 Context Policy, namespace cap |
| v7 | What do I owe the human? | Identity Coherence, Cognitive Autonomy, EVALUATIVE domain |
| v7.1 | Empirically hardened? | UAI 0.40 floor, Continuity Drill |
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
