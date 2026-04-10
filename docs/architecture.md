# MNEMOS Architecture Reference

**Version:** mnemos-lite v0.7
**Status:** Behavioral tuning phase — architecture stable

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

## The 14 Layers

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

### L3 — Semantic Store
Async consolidation. Beliefs graduate here from episodic records.

- Domain-typed claims
- Self-consistency veracity scoring
- Version diffing + drift alerts

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

### L6 — Audit Log
Immutable append-only event log.

- Cryptographically signed records
- Performance events
- All FM Register entries written here

### L7 — Grounding Oracle
External validation. **FACTUAL domain only.**

- Domain-gated: preferences and identity never sent to oracle
- Self-consistency model for preference validation (internal only)

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

### L11 — Arbitration Engine
Cross-path conflict resolution.

- 3 strategies with Strategy Diversity Budget (max 70% any single strategy)
- Risk Mode Momentum: escalating exit cost prevents oscillation
- SLAs per conflict type

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

---

## Belief Data Model

Structured belief fields (introduced v7, FM-76).

```python
@dataclass
class Belief:
    trait:             str      # What aspect (e.g. 'response_style')
    value:             str      # Observed value (e.g. 'concise')
    context:           str      # When/where it applies — hard-gated in retrieval
    exceptions:        List     # Noted exceptions
    content:           str      # Auto-generated label
    domain:            Domain   # See domains below
    namespace:         str      # work / health / personal / research / ...
    alpha:             float    # Beta distribution alpha
    beta_:             float    # Beta distribution beta
    evidence_count:    int      # Total interactions this belief appeared in
    last_confirmed:    float    # Timestamp of last explicit confirmation
    last_contradicted: float    # Timestamp of last contradiction
    source_text:       str      # Evidence this belief was drawn from
```

`confidence = alpha / (alpha + beta_)`

The key insight: `'concise at work'` and `'detailed when learning'` are two non-contradictory beliefs about the same trait. The `context` field is a hard gate in retrieval — not a soft hint.

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
