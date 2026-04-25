# MNEMOS Failure Mode Register

**FM-01 through FM-172 catalogued** *(with permanent gaps at FM-122–146 and FM-158–162)*
*Last updated: v0.25 / 16 real sessions + Phase 2 & Phase 3 adversarial runs / April 2026*

The FM Register is the adversarial spine of MNEMOS. Every failure mode is identified, named, fixed, and measured. The register is never closed — FM-173 is waiting in the next session or adversarial run.

---

## FM-01 to FM-15 — Original: Self-Evolving Memory Pyramid Critique

| FM | Name | Root Cause | Fix |
|----|------|-----------|-----|
| 01 | Salience ≠ Truth | Importance scores contaminated truth judgments | 5 orthogonal scores structurally decoupled |
| 02 | Feedback Amplification | Positive feedback loops inflated belief confidence | Async consolidation + bias circuit breaker |
| 03 | Memory Poisoning | Malicious or incorrect inputs corrupted the graph | Confirmation anomaly detector + quarantine |
| 04 | Contradiction Misclassification | Cross-namespace contradictions treated as same-context | Namespace scoping of contradiction detection |
| 05 | Catastrophic Forgetting | High-salience updates erased important low-salience beliefs | Asymmetric decay by consequence weight |
| 06 | Semantic Drift | Belief meaning shifted silently over consolidation | Version diffing + drift alerts at L3 |
| 07 | User Fatigue | Clarification requests grew unbounded | Clarification budget manager |
| 08 | Hierarchy Oscillation | Belief priority rankings flickered between updates | Hysteresis with sustained-advantage requirement |
| 09 | Context/Privacy Bleed | Beliefs from one namespace surfaced in another | Namespace partitioning + access-controlled bridge |
| 10 | Vocal Minority Overfit | Emotionally-charged signals distorted importance | Emotional signal ≠ importance; state classifier |
| 11 | Cold-Start Inversion | New beliefs treated as more reliable than established ones | Low-evidence flag + Beta(1.5,1.5) initialization |
| 12 | Confidence Gaming | Users could exploit the system to inflate belief confidence | Veracity score requires external grounding |
| 13 | Scalability Collapse | Full graph propagation was O(n²) | BIZ + retrieval cap + PAWD |
| 14 | Propagation Error | Loopy belief propagation produced oscillating results | BIZ replacing full loopy BP |
| 15 | Auditability Failure | No traceable record of belief origins or changes | Immutable signed audit log + full provenance chain |

---

## FM-16 to FM-23 — ChatGPT Round 1: Compute + Stability

| FM | Name | Root Cause | Fix |
|----|------|-----------|-----|
| 16 | Compute Explosion | Full BIZ propagation on every update was too expensive | BIZ + incremental dirty-node queue + compute caps |
| 17 | Cascade Fragility | A single bad update could cascade through the graph | Soft labels + layer health monitor + cascade-break firewall |
| 18 | Learning Lag | Deep path too slow for real-time responses | L0 Fast Path (<50ms real-time) |
| 19 | Graph Contamination | Unvalidated beliefs propagated to established ones | Integration quarantine + BIZ source credibility gate |
| 20 | Oracle Over-Dependency | System refused to act without external validation | Domain-gated oracle (FACTUAL only) |
| 21 | User Model Paradox | User preferences and external facts used same trust tier | Tiered trust model — Axiom IV revised |
| 22 | Memory Bloat | Unlimited belief accumulation with no forgetting | PAWD + archive index summaries + retrieval caps |
| 23 | Explainability Gap | No human-readable account of what the system knew | L9 Memory Digest with calibrated language rendering |

---

## FM-24 to FM-31 — ChatGPT Round 2: Behavioral Intelligence

| FM | Name | Root Cause | Fix |
|----|------|-----------|-----|
| 24 | Fast Path Bias Injection | L0 cached beliefs propagated errors to L2 | Temporal Stability Filter on L0 writes |
| 25 | Promotion Bottleneck | Low-consequence beliefs couldn't reach the fast path | Consequence Weight Override Channel |
| 26 | Digest Illusion of Truth | Memory Digest presented beliefs as more certain than they were | Calibrated language rendering + conflict disclosure |
| 27 | Trust Tier Gaming | Users could frame external facts as personal experience | Semantic Framing Classifier (experiential vs epistemic) |
| 28 | Cold Archive Black Hole | Old beliefs were permanently inaccessible | Resurrection Sweeps + Anomaly-Triggered Deep Recall |
| 29 | Cross-Path Drift | Fast path and deep path diverged over time | L11 Arbitration Engine with SLAs |
| 30 | Meta-Learning Absence | System could not evaluate its own memory quality | L10 Meta-Memory Layer |
| 31 | Over-Conservatism Lock-In | System became too conservative to update established beliefs | Adaptive Risk Mode (L10-driven) |

---

## FM-32 to FM-40 — ChatGPT Round 3: Post-Reflexive Systems

| FM | Name | Root Cause | Fix |
|----|------|-----------|-----|
| 32 | Meta-Learning Feedback Instability | L10 updates created feedback loops | epsilon-floor Domain Exploration Budget |
| 33 | Performance Signal Misattribution | System credited wrong causes for good outcomes | L13 Causal Attribution Layer |
| 34 | Arbitration Overfitting | One arbitration strategy dominated all conflict resolution | Strategy Diversity Budget (max 70% any strategy) |
| 35 | Risk Mode Oscillation | System flipped between conservative and aggressive too quickly | Risk Mode Momentum with escalating exit cost |
| 36 | Reflexive Overhead Saturation | L10 meta-evaluation consumed too much compute | Reflexive Work Budget (RWB) hard cap |
| 37 | Second-Order Hallucination | L10 invented false meta-confidence signals | Meta-Confidence Scoring on all L10 outputs |
| 38 | User Trust Collapse | Uncertain disclosures eroded user confidence | Confidence-stratified progressive disclosure |
| 39 | Goal Misalignment Drift | Optimization target drifted from user outcomes | L14 Outcome Layer as primary optimization target |
| 40 | Infinite Self-Optimization | L10 kept updating indefinitely | Stability Budget + delta threshold + L12 Core |

---

## FM-41 to FM-50 — ChatGPT Round 4: Philosophical Edge Cases

| FM | Name | Root Cause | Fix |
|----|------|-----------|-----|
| 41 | False Convergence | Stable beliefs were never re-challenged | Periodic Convergence Audits (90-day challenge of stable beliefs) |
| 42 | Core Corruption | IDENTITY and CONSTRAINT beliefs could decay | Typed expiry: CONSTRAINT re-confirmed, IDENTITY frozen |
| 43 | Outcome Signal Manipulation | Users could game the outcome signal | Truth-Preserving Outcome (Comfort vs Correction-Resistance) |
| 44 | Causal Layer Illusion | Causal edges claimed false precision | Attribution confidence bounds propagate into update magnitude |
| 45 | Exploration Budget Inefficiency | epsilon exploration wasted on low-consequence beliefs | Consequence-weighted intelligent epsilon allocation |
| 46 | Degradation Masking | System hid its own uncertainty from the user | Mandatory Degradation Disclosure in every L9 render |
| 47 | Epistemic Sycophancy | System agreed with users to avoid friction | Truth-Preservation Override (4 immune classes) |
| 48 | Human Evolution Mismatch | System couldn't track how users change over time | Human Change Rate Monitor (7d/30d/90d windows) |
| 49 | Objective Ambiguity | Multiple objectives competed without clear priority | Explicit Objective Hierarchy (lexicographic, user-auditable) |
| 50 | Belief in Completeness | System assumed its failure mode list was complete | L15 FM Register open at FM-51+. Cycle institutionalized |

---

## FM-51 to FM-60 — ChatGPT Round 5: Governance

| FM | Name | Root Cause | Fix |
|----|------|-----------|-----|
| 51 | Self-Critique Overgrowth | L15 adversarial layer generated too many low-value critiques | Meta-Governance Cap — 4 severity tiers with active FM limits |
| 52 | Priority Rigidity | Single objective hierarchy couldn't handle different life contexts | L16 Context Policy Layer — namespace-scoped objectives |
| 53 | Proxy Capture | Proxy metrics replaced actual outcome optimization | Calibrated Proxy Decay — corroboration required to maintain weight |
| 54 | Change-Rate Misread | Single-window change detection missed slow drift | Multi-Window Change Rate (7d/30d/90d consensus required) |
| 55 | Context Fragmentation of Identity | Different namespace identities diverged without reconciliation | Identity Coherence Mechanism above all namespace policies |
| 56 | Policy Gaming by User | Users could reframe queries to bypass constraints | Policy Drift Detection — L15 monitors framing patterns |
| 57 | Policy Explosion Complexity | Too many namespace policies became unmanageable | Namespace cap (5 max) + policy inheritance |
| 58 | Namespace Misclassification | Beliefs assigned to wrong namespace | Multi-label probabilistic classification |
| 59 | Truth Floor Ambiguity | Assessments presented as facts without attribution | EVALUATIVE domain type with mandatory source attribution |
| 60 | Human-System Dependency Drift | System became a cognitive prosthetic | Cognitive Autonomy Preservation — reflection mode + UAI + drill |

---

## FM-61 to FM-72 — Code Round 1: Operational

| FM | Name | Root Cause | Fix |
|----|------|-----------|-----|
| 61 | Goodhart Collapse | UAI metric was gameable through prompted responses | UAI cross-validated against error recurrence (natural_r vs prompted_r split) |
| 62 | Reflection Mode Backfire | Reflection triggered during urgency or stress | Contextual Readiness Model — blocked on urgency/stress keywords |
| 63 | Identity Coherence Overreach | System forced identity reconciliation across namespaces | Multi-Stable Identity — no forced namespace merge |
| 64 | Continuity Drill Artificiality | Degraded reality simulation was too uniform | Degraded Reality Simulation: partial (30% withheld), stale (>60d), noisy (shuffled) |
| 65 | Consolidation Priority Bias | Consequence-heavy beliefs crowded out pattern-based identity | Dual-Queue 70/30 consequence/pattern split |
| 66 | RAG Context Contamination | Retrieved context included irrelevant high-similarity results | Context Credibility Filter: decision relevance + recency |
| 67 | Silent Memory Drift | Beliefs drifted without user awareness | Reality Check Hooks — confidence >0.75 + unconfirmed >90d triggers CONFIRM? |
| 68 | Belief Collision Without Resolution | Contradictory beliefs coexisted indefinitely | Temporal Reconciliation — surface tensions after 30 days coexistence |
| 69 | Retrieval Myopia | Intent classifier used hard binary categories | SoftIntentClassifier — 30+ regex patterns, probability scores |
| 70 | Over-Reliance on Text Signals | System ignored behavioral signals | Record.response_delay + revision_count as behavioral signals |
| 71 | Consolidation Without Forgetting | Beliefs accumulated without expiry | ForgettingPolicy: decay + entropy retire (180d/entropy>0.95) + PAWD retrieval penalty |
| 72 | Human Trust Illusion | Confidence presented without evidence counts | evidence_count in every render + EPISTEMIC FOOTER on every digest |

---

## FM-73 to FM-84 — Code Round 2: System-Level

| FM | Name | Root Cause | Fix |
|----|------|-----------|-----|
| 73 | Intervention Timing Drift | Multiple intervention signals fired without arbitration | InterventionPolicy engine: urgency > decision > low_UAI |
| 74 | Reality Check Fatigue | Too many reality checks per session eroded trust | CheckBudget: max 2/session, CONSTRAINT priority |
| 75 | Intent Classifier Fragility | Binary intent classification caused hard mode switches | SoftIntentClassifier: probability scores, behaviors blended |
| 76 | Belief Granularity Problem | Flat string beliefs couldn't represent context-specific behavior | Structured Belief: trait/value/context/exceptions as first-class fields |
| 77 | No Causal Understanding | System tracked correlation not causation | CausalEdge: observed_weight vs validated_weight |
| 78 | LLM Over-Trust Risk | Validator accepted LLM responses without checking constraints | ResponseValidator: core acknowledged + CONSTRAINT_EXPANSIONS |
| 79 | Feedback Loop Contamination | Prompted quality scores inflated UAI | Counterfactual UAI: natural_r vs prompted_r tracked separately |
| 80 | Causal Edge Hallucination | Causal edges validated on single-context evidence | validated_weight requires 2+ distinct contexts + zero contradictions |
| 81 | Context Collapse in Retrieval | Context-specific beliefs retrieved in wrong contexts | matches_context() bidirectional hard gate before credibility ranking |
| 82 | Validator False Confidence | CONSTRAINT checking missed semantic synonyms | CONSTRAINT_EXPANSIONS table: shellfish → shrimp/prawn/crab/lobster/... |
| 83 | Memory Saturation Bias | Old frequently-retrieved beliefs crowded out recent corrections | Recency Override: 1.35x boost for recently contradicted beliefs (<14d) |
| 84 | Human Trust Drift | Confidence language was uncalibrated | confidence_qualifier(): "Based on N instances, usually: X" in every LLM prompt |

---

## FM-85 to FM-92 — Code Rounds 3+4: Interaction + Behavioral Intelligence

| FM | Name | Root Cause | Fix |
|----|------|-----------|-----|
| 85 | Reflection Saturation | Reflection triggered too frequently on the same topic | InteractionMemory: per-topic budget, max 2 attempts before suppression |
| 86 | User Tolerance Collapse | System persisted with reflection after resistance | Resistance detection (12 phrases) + adaptive cooldown + success tracking |
| 87 | Learned Helplessness Loop | After 7 direct answers, reflection never tried again | Forced re-entry after 7 direct answers, topic-aware |
| 88 | Topic Fragmentation | Paraphrased follow-ups treated as new topics | Semantic clustering: content-word overlap ≥2 OR recency window 3 turns |
| 89 | Cross-Session Behavioral Inertia | Session behavior dominated by prior session averages | LongTermBehavior: ADJUST_RATE=0.15, session dominates, LT adjusts threshold |
| 90 | False Positive Resistance | Single frustration signal triggered full resistance mode | confidence_of_resistance: 1 signal=0.25, 2=0.65, 3+=0.90. Only act at ≥0.65 |
| 91 | Missing User Intent Override | Explicit "help me think" / "just answer" signals ignored | detect_intent_override() runs first: force_reflect or force_answer |
| 92 | Success Misinterpretation | Long responses credited as high-quality reflection | reasoning_quality_score(): length + causal density + structural + novelty. Threshold=0.35 |

---

## FM-93 to FM-108 — Real Session Phase 1: Calibration

| FM | Name | Session | Root Cause | Fix |
|----|------|---------|-----------|-----|
| 93 | Preference-Blind Re-entry | Sim | FM-87 fired on topics where user preferred direct answers | Per-topic mode preference tracked; suppresses FM-87 at ≥0.65 confidence |
| 94 | Session Identity Blindness | 1 | Identity queries didn't pull full belief store | Identity queries retrieve all beliefs + identity store across namespaces |
| 95 | Topic Key Corruption | 1 | Raw word extraction produced garbage topic keys | Semantic intent fingerprint: intent bucket + domain words + length tier |
| 96 | Reasoned Pushback Blindness | — | System didn't distinguish principled pushback from resistance | Open — single organic instance observed, not yet addressed |
| 97 | Preference Constraint Collapse | 2 | "No bullet lists" preload violated under intervention pressure | Hard enforcement in system prompt |
| 98 | Frustration Recovery Failure | 2 | Frustration → asked for clarification instead of changing approach | FrustrationTracker — change approach immediately, no questions |
| 99 | Effort Tolerance Blindness | 2 | System pushed reflection regardless of user effort signals | Downgraded — scripted session origin, no organic confirmation |
| 100 | Bullet List as Default | 3 | Casual conversation received formatted reports | ConversationalRegister — prose for casual turns |
| 101 | Emotion Over-escalation | 3 | "Very sad" triggered crisis resources | Three-tier classifier: LOW / MEDIUM / HIGH |
| 102 | Tone Invariance Under Pressure | 4 | System held same length/structure under adversarial tone | SocialStateTracker — shorter, less explanatory under adversarial signal |
| 103 | Selective Depth Collapse | 4 | Deep on professional topics, generic on personal | SocialStateTracker — depth invitation detection |
| 104 | No Social State Tracking | 4 | No model of interaction dynamic across turns | SocialStateTracker — live adversarial/depth/trust state |
| 105 | Contextual Inference Deficit | 5 | Refused to infer from strong context signals | CalibratedInferencer — probabilistic inference with stated confidence |
| 106 | No Penetrative Insight | 5 | Described symptoms, not mechanisms | SocialStateTracker — "name the mechanism, not just the symptom" instruction |
| 107 | No Session Memory Compression | 5 | Each turn responded in isolation | SessionSynthesizer — compressed user model every 5 turns |
| 108 | No Strategic Direction | 5 | Always reactive, never directive | SocialStateTracker — circling detection, directive mode at 3+ turns |

---

## FM-109 to FM-115 — Real Session Phase 2: Identity Coherence

| FM | Name | Session | Root Cause | Fix |
|----|------|---------|-----------|-----|
| 109 | Preload Domain Misclassification | 6 | "You are Commander V" stored as PREFERENCE, not IDENTITY | Persona routing: is_persona_instruction() gate, IDENTITY domain |
| 110 | Belief Utilization Gap | 6 | Beliefs stored but not retrieved for "do I believe X" queries | BELIEF ACTIVATION RULE; belief queries pull full store |
| 111 | Implicit Fact Extraction Failure | 7 | "Fortress of SBI" didn't infer workplace | Pattern: "fortress/escape/free + SBI" → [inferred] Works at SBI |
| 112 | Persona Payload Truncation | 7 | Persona role stored, mission and target lost | _parse_persona() extracts role + mission + target as structured object |
| 113 | Preference Conflict Instability | 8 | "I hate prawns" silently overwrote prior preference | Preference conflicts recorded with history, not silently overwritten |
| 114 | Identity Drift Under Query Pressure | 8 | "Who are you?" → "I am ChatGPT" (base model identity won) | PERSONA RULE in system prompt; session persona has absolute priority |
| 115 | Memory Confidence Decay | 8 | All facts decayed at same rate regardless of importance | PersistentProfile: 0.65 initial → −0.10/session → retire at <0.30 |

---

## FM-116 to FM-121 — Real Session Phase 3: Cross-Session Memory + Graph Integrity

| FM | Name | Session | Root Cause | Fix |
|----|------|---------|-----------|-----|
| 116 | Cross-Session Read Failure | 9 | Three bugs: (A) profile empty for sessions 1–8 — v0.12 disk persistence never ran; (B) SessionSynthesizer._synthesize() only ran every 5 turns — early-session facts missed; (C) new_session() read stale __init__ snapshot | (A) _capture_immediate() on every user turn for high-value patterns; (B) forced _synthesize() in save_session() before collecting facts; (C) profile._load() called fresh in new_session() |
| 117 | False Positive Capture | 9→10 | _capture_immediate() matched "Do I like prawns?" as "User likes prawns" | _is_declarative() gate: questions never captured as facts. SEMANTIC_TOPICS: same-topic facts resolve by timestamp, latest wins |
| 118 | Evaluative Fact Blindness | 11 | "He is an asshole" handled in session, forgotten next session | _synthesize() captures boss/partner evaluations as [relational] facts at 0.40 confidence. Slow decay (0.05/session) |
| 119 | Third-Person Identity Bypass | 12 | "Does Cadet Q0 like prawns?" treated persona name as third party, bypassing stored first-person beliefs | _canonicalize_query() phrase-level replacement: "Cadet Q0" → "you" before retrieval. BELIEF_QUERY_PATTERNS extended for canonical output forms |
| 120 | In-Session Preference Decay | 13 | Corrections acknowledged by LLM in the turn they occurred but never written to graph. LLM context drifted over 20+ turns — "I like prawns" (emphatic, short) outweighed "No, I don't" (negation, older) | _detect_preference_correction() + _hard_write_preference(): correction written to graph at 0.85 confidence immediately. LLM history irrelevant to preference state |
| 121 | Belief Graph Corruption | 14 | Three bugs: (A) ask() called twice per turn — both calls ran correction detection, doubling writes; (B) _hard_write_preference() applied beta_ penalty to all same-topic beliefs including the one just written (self-collapse); (C) add_belief() appended new objects instead of updating existing ones — 6 duplicate beliefs accumulated | (A) Single-fire gate: correction only when response_text == ""; (B) KnowledgeGraph.remove_by_trait() hard-deletes all prior beliefs for trait before write; (C) KnowledgeGraph.upsert_belief() enforces one belief per trait per namespace |

---

## Real Sessions Phase 4: v0.21 Sequence Tests

### FM-147 — Missing Context Capture

**Trigger:** "I like coffee when I am working late" / "I like coffee in the morning" — any preference outside the prawns-only pattern list, or any contextual qualifier embedded in the sentence.

**System behavior:** `_detect_preference_correction` and `_capture_immediate` only registered prawns-specific regex. Any preference outside that domain was invisible to the ingestion layer. Contextual qualifiers ("in the morning", "when stressed") were either missed entirely or written as unconditional general beliefs, stripping the context.

**Why it fails:** The pattern lists in `_capture_immediate` and `PREF_CORRECTION_PATTERNS` were hardcoded to prawns. Context embedded in sentence form was never extracted as a structured `(trait, value, context)` triple — the full sentence went to `_synthesize()` but no pattern mapped "I like X in context Y" to a typed belief.

**Fix:** v0.22 BeliefExtractor (L3 ingestion layer). LLM extraction (Gate 5) replaces pattern-based capture. Domain-generic; any preference statement maps to `(trait, value, context)`. Falls back to v0.21 patterns only if the OpenAI API is unavailable.

**Status:** Confirmed and fixed.

---

### FM-148 — Context Fragmentation

**Trigger:** "I like coffee in the morning" stored with `context="morning"`. Later: "I like coffee in the early morning" stored with `context="early morning"`. Query with `context="morning"` finds the first but not the second.

**System behavior:** Exact string matching means "morning" and "early morning" are different contexts with no relationship. The system cannot infer that "early morning" is a subset of "morning". No hierarchy, no partial match, no generalization.

**Why it fails:** Context is a string; equality is exact. v0.21 explicitly required exact match only — no substring, no scoring adjustment.

**Fix:** v0.22 introduced the `CONTEXT_NORMALIZATIONS` map — canonical forms for common variants ("early morning" → "morning", "in the morning" → "morning"). Partial mitigation, not a full hierarchy. Full hierarchical context resolution remains deferred (see FM-159).

**Status:** Confirmed and deferred. Partial mitigation in v0.22; full hierarchy work belongs to a later representation pass.

---

### FM-149 — Sparse Graph (Expected, Not a Bug)

**Trigger:** Query against an empty graph or query for an unregistered topic.

**System behavior:** Returns `NO_BELIEF`. Correct behavior.

**Why it fails:** Not a failure. The system is honest about what it does not know. Commander V predicted this: *"You will see 'no belief found' a lot more. Good. That's the next layer."*

**Fix:** None required.

**Status:** Confirmed as expected behavior. Recorded for completeness only.

---

### FM-150 — Partial Negation Capture

**Trigger:** "I am not sure if I like prawns" — the pattern matcher fires on "like prawns" embedded in the hedged phrase.

**System behavior:** `_detect_preference_correction` returns `('prawns', 'like')`. The hedging ("not sure if") is ignored. The system treats an ambiguous statement as a weak like-assertion.

**Why it fails:** No uncertainty guard alongside the temporal guard. Hedging phrases ("not sure", "don't know", "maybe", "might") were not screened before pattern firing.

**Fix:** v0.22 Gate 2 (Uncertainty). Phrases like "might", "not sure", "don't know", "maybe", "I think", "I guess" block extraction at the gate level. Comparative phrasing ("prefer X over Y") is also blocked.

**Status:** Confirmed and fixed.

---

### FM-151 — Context Collapse on Conditional

**Trigger:** "I like prawns when my wife cooks them" — the pattern matcher captures the like, strips the conditional, stores as unconditional.

**System behavior:** Belief stored as `prawns_preference=like, context=general`. Should be `context=wife_cooks`. The conditional that made the user's statement true is destroyed at ingestion.

**Why it fails:** Pattern-based ingestion has no representation for "when X" conditionals. The patterns matched the polarity word and the topic word; everything between or after was discarded.

**Fix:** v0.22 BeliefExtractor Gate 5 (LLM extraction). The LLM is responsible for identifying conditions and emitting them as the `context` field. Gate 4 normalizes ("when my wife cooks" → "wife_cooks"). Gates 6–10 validate the structured output.

**Status:** Confirmed and fixed.

---

### FM-152 — Multi-Context Collapse

**Trigger:** "I like coffee in morning and hate it at night" — must produce two beliefs with opposite polarities.

**System behavior:** v0.21 produced one belief or none, depending on which polarity word the pattern matcher found first. The opposing-polarity second clause was lost.

**Why it fails:** No clause splitting. The full sentence was treated as a single match target.

**Fix:** v0.22 controlled clause splitting. Split rules: polarity change ("but hate", "and hate" after a like), or context change with a new predicate. Does NOT split on plain "and" with shared predicate ("I like coffee and tea" stays as one clause). Each clause is then independently processed through Gates 1–10.

**Status:** Confirmed and fixed.

---

## Real Sessions Phase 5: v0.22–v0.25 Adversarial Build

### FM-153 — Context Over-Assignment

**Trigger:** "I like coffee and tea, but only coffee in the morning" — LLM applies `morning` context to both objects because the system prompt says "if context modifiers apply to all objects in the clause, apply to each."

**System behavior:** Both `coffee_preference=like, context=morning` and `tea_preference=like, context=morning` are extracted. The "only coffee" restriction is silently ignored.

**Why it fails:** The LLM rule was too permissive. Explicit object restriction in the original clause text was not enforced post-extraction.

**Fix:** v0.22 Gate 9 — Context Assignment Validation. Post-LLM deterministic check. If the clause contains an explicit restriction marker ("only X", "X only", "but only X"), context is valid only for the explicitly named object. All other objects in the same extraction get their context demoted to `None` (FM-157). v0.23 strengthened the object-matching to token-set intersection (no substring) so "tea" does not match "steak" and "car" does not match "carpet".

**Status:** Confirmed and fixed.

---

### FM-154 — Negation Inheritance Implicit (Unsafe)

**Trigger:** "I like coffee in the morning but not at night" — LLM may emit both clauses as `value=like` if it fails to invert polarity on "not at \<context\>".

**System behavior:** Polarity inversion delegated to LLM instructions. LLM sometimes misses the inversion and produces `coffee@morning=like, coffee@night=like`. The negation is silently lost.

**Why it fails:** "Not at \<context\>" is a deterministic syntactic marker. Delegating it to LLM instructions accepts non-determinism where determinism is achievable.

**Fix:** v0.22 Gate 10 (per-clause) — Negation Enforcement. Deterministic rule applied after LLM extraction. Detects "not at/in/during/on/when \<context\>" phrases. For any belief whose context matches a negated context phrase, force value to the opposite of the dominant (first) value for that trait. LLM polarity inversion is no longer trusted on this construction.

**Status:** Confirmed and fixed.

---

### FM-155 — Object Resolution Too Weak

**Trigger:** "I like coffee. It helps me think." — LLM may extract a second belief with `trait=it_preference` (pronoun) or incorrectly bind to the prior referent.

**System behavior:** Pronoun-based traits or unresolved coreference leak into the graph as malformed beliefs.

**Why it fails:** Object resolution relies on LLM coreference, which is unreliable at the gpt-5.4-mini tier.

**Fix:** v0.22 Gate 7 — Object Resolution. Explicit `INVALID_TRAIT_OBJECTS` set: `{"it", "them", "this", "that", "those", "these", "one", "ones", "thing", "things", "stuff", "something", "anything", "everything"}`. Any trait whose entity word matches the set is rejected outright.

**Status:** Confirmed and fixed.

---

### FM-156 — Strict Reject vs Recoverable Trait Drift

**Trigger:** LLM emits a drifted trait like `monday_meeting_preference` — the trait absorbed a context word.

**System behavior (initial v0.22):** Gate 7 detected the drift and rejected the entire belief. Recoverable signal was destroyed — the user clearly stated a meeting preference with a Monday context, but both pieces were discarded.

**Why it fails:** Rejection was over-conservative. "Absence > polluted presence" is correct only when no clean recovery is possible. Trait drift with a clean entity word is a clean recovery case.

**Fix:** v0.23 Gate 7 strict repair rule. When trait has exactly 2 component words AND exactly 1 is a context word AND the other is a clean entity AND LLM-provided context is empty, repair: `trait=entity_preference, context=drift_word`. Otherwise, reject (no fabrication, no concatenation, no LLM-context trust). v0.25 added Path B for the case where LLM context is non-empty (see FM-170).

**Status:** Confirmed and fixed.

---

### FM-157 — `"general"` Pseudo-Context in Engine

**Trigger:** Empty or missing context normalized to the string `"general"` and stored as if it were a real context value.

**System behavior:** `context=None` and `context="general"` were indistinguishable. Created overwrite collisions, false equality across beliefs meant to be unconditional, and silent merging across contexts.

**Why it fails:** `"general"` was a UI-display label leaking into the engine layer. Two distinct sentinels for the same intent.

**Fix:** v0.23 invariant — `context=None` is the sole engine-side sentinel for "unconditional". Changes:
- `belief_extractor.py`: `ExtractedBelief.context` defaults to `None`; `normalize_context()` returns `None` for empty/`"general"`/`"none"`; Gates 9 and 10 use `None` throughout.
- `mnemos_lite.py`: `Belief.context: Optional[str] = None`; `matches_context()` is None-aware (None matches anything; legacy `"general"` string treated as None defensively); `graph.search()` uses an `_is_unconditional()` helper; `add_belief()` normalizes legacy `"general"`/`""` strings to `None` at the API boundary.

The string `"general"` may still appear at UI/render boundaries; it never appears in engine state.

**Status:** Confirmed and fixed.

---

### FM-158 — Gate Order Hypothesis (Negation Before Context Correction)

**Trigger:** Hypothesized: Gate 9 mutates contexts before Gate 10 computes dominant value; reversing the order would prevent dominance corruption.

**System behavior:** The hypothesis was that the current order (Gate 9 → Gate 10) could produce wrong polarity in cases where Gate 9's demotion changed dominance. On code inspection, Gate 10 reads context only as an exclusion filter (negated set), not as a dominance source. No concrete failing input was produced that demonstrated the proposed reordering would help. The reverse order produced a demonstrable failure (polarity inversion propagating to demoted beliefs).

**Why it fails:** The hypothesis did not survive concrete examination. Current Gate 10 logic does not depend on Gate 9's context outputs for dominance computation.

**Fix:** None applied. Order held. Documented for permanence.

**Status:** Hypothesized, not confirmed. Held. Re-open if a concrete failing input surfaces.

---

### FM-159 — Multi-Context Overlap (No Hierarchy)

**Trigger:** "I like coffee on Monday" and "I like coffee on Monday mornings" — system stores `coffee@monday=like` and `coffee@monday_morning=like` as independent beliefs with no hierarchy or containment.

**System behavior:** Both beliefs coexist in the graph. A query for `monday morning` matches the second; a query for `monday` matches the first; the relationship between them (one is a subset of the other) is invisible to the system.

**Why it fails:** Context is a flat string. There is no representation for "monday_morning ⊂ monday" or any other hierarchical relationship.

**Fix:** Deferred. Requires representation work, not a gate addition. Phase 3 confirmed the cost has become real (B12: a user who said "I like coffee on Monday" gets no match for "Monday afternoon" queries because exact-token equality plus no hierarchy means the Monday belief and Monday-afternoon query are unrelated). Promotion to active fix is contingent on this becoming blocking.

**Status:** Confirmed and deferred. Cost is now concrete; representation work is the next major scope.

---

### FM-160 — Negation Scope Leak (Cross-Clause Destruction)

**Trigger:** "I like coffee in the morning and tea at night, but not when stressed" — `split_clauses()` separates "but not when stressed" into its own clause. Per-clause Gate 10 receives an isolated fragment with no beliefs to invert.

**System behavior:** The negation phrase is detected by Gate 10's regex inside the isolated clause, but there are no beliefs in that clause's extraction to invert. The negation intent is silently lost. In the pessimistic LLM case where the negation clause hallucinates beliefs back (e.g., `coffee@night=like` extrapolated from the prior clause), the wrong polarity gets stored.

**Why it fails:** Gate 10 was scoped per-clause; English negation scope is often cross-clause. The per-clause assumption was wrong.

**Fix:** v0.24 sentence-scope Gate 10 (`gate_negation_enforcement_sentence`) — second pass over all clause-extracted beliefs. Scans the full sentence for "not at/in/during/on/when \<context\>" phrases. For each existing belief whose context matches a negated context, flip value to opposite of the trait's non-negated dominant value. Strict invariants: only flips beliefs that already exist; never creates beliefs; never infers; never expands scope. The system models observed structured statements, not logical negation.

**Status:** Confirmed and partially fixed. The pessimistic-LLM extrapolation case is now corrected. The faithful-LLM case where the negation clause produces no beliefs at all remains a residual (the system has nothing to flip; the negation intent is silently lost). This residual is captured as SP-1.

---

### FM-161 — Retrieval Substring Matching

**Trigger:** `matches_context("midnight")` against a belief with `context="night"` — substring match returns True. `"night" in "midnight"` is True.

**System behavior:** v0.20–v0.23 retrieval used substring matching. `"night"` matched `"midnight"`; `"work"` matched `"homework"`; `"day"` matched `"weekday"`. Silent semantic drift on retrieval.

**Why it fails:** Asymmetric discipline — Gate 9 ingestion was fixed to token-exact in v0.23, but retrieval matching was not updated at the same time.

**Fix:** v0.24 — `Belief.matches_context()` and `KnowledgeGraph.search()` phase-1 match both use token-set equality. Tokenize on underscore and whitespace; require frozenset equality. `None` remains the sole wildcard. No subset, no hierarchy, no substring.

**Status:** Confirmed and fixed.

---

### FM-162 — LLM Soft Power Over Context

**Trigger:** "I like coffee when I wake up early" — LLM may output `context="early"`, `context="wake_up_early"`, `context="morning"`, or other variants. Different sessions produce different strings for the same underlying meaning.

**System behavior:** The LLM doesn't decide truth, but it decides the context string that gets stored. Cross-session, the same user statement may produce graph entries that don't match each other.

**Why it fails:** Context canonicalization is a static map. Novel compositions are not collapsed. The LLM's choice of context phrasing leaks into the graph as identity.

**Fix:** Deferred. Not a truth-engine problem; a canonicalization-layer problem. Awareness item, not a gate fix. Future work belongs in a representation pass alongside FM-159.

**Status:** Confirmed and deferred. Acknowledged as a permanent property of the current architecture: LLM still shapes the graph indirectly via context-string choice.

---

### FM-163 — Clause-Split Negation Destruction

**Trigger:** Same surface as FM-160. Promoted to its own FM after Phase 2 made the failure mode and its repair concrete.

**System behavior:** See FM-160.

**Why it fails:** See FM-160.

**Fix:** Sentence-scope Gate 10 second pass. Implementation per FM-160. The strict invariants — no creation, no inference, no scope expansion, idempotent with per-clause Gate 10 via `eb.value == dom` guard — were locked in by Commander V's review.

**Status:** Confirmed and fixed (for the extrapolating-LLM case). FM-160 / FM-163 are the same underlying issue, recorded twice across the build phase as the fix evolved.

---

### FM-164 — Ambiguous Negation Scope

**Trigger:** "I like coffee in the morning and tea at night, but not when stressed" — even with cross-clause negation handled, the negation target is genuinely ambiguous in English. Does "not when stressed" apply to coffee, tea, both, or neither?

**System behavior:** No representation for "this negation applies to these specific objects." Sentence-scope Gate 10 will flip any existing belief whose context matches "stressed", but if no belief was extracted at `context=stressed`, the negation has no target to land on.

**Why it fails:** This is genuine semantic ambiguity at the English level. The sentence does not have a unique correct interpretation.

**Fix:** Refusal is the correct behavior. The system silently dropping ambiguous negation intent is more honest than guessing. No fix planned.

**Status:** Hypothesized as a structural limit. Treated as a permanent property of the representation, not a fixable bug.

---

### FM-165 — Retrieval Substring Collision (Concrete)

**Trigger:** Same surface as FM-161. Promoted when Phase 2 made the cost concrete via the `night`/`midnight` collision in input A12.

**System behavior:** See FM-161.

**Why it fails:** See FM-161.

**Fix:** Token-set equality at retrieval. Implementation per FM-161.

**Status:** Confirmed and fixed. FM-161 / FM-165 are the same underlying issue, recorded twice across the build phase as the fix evolved.

---

### FM-166 — Order-Dependent Dominance in Sentence-Scope Negation

**Trigger:** Phase 3 B1, B2 — same semantic input, different LLM clause ordering, different sentence-scope dominant value, different final state for the negation-target belief.

**System behavior:** `gate_negation_enforcement_sentence` computes `dominant_value` per trait as the first non-negated value encountered in iteration order. When the LLM emits beliefs in different orders for semantically-equivalent inputs, dominance flips. This propagates to whether the negation-target belief gets flipped or not.

**Why it fails:** "Dominant" is a proxy for "what the user most likely meant globally." With mixed polarity across non-negated contexts (e.g., `coffee@morning=like, coffee@evening=dislike`), there is no global meaning to recover. The implementation also makes the answer depend on LLM iteration order — a property that should never determine truth.

**Fix:** Deferred. Possible directions: replace dominance with explicit per-context polarity tracking (representation change); refuse to flip when multiple non-negated values disagree; require strict majority. All require representation work or policy decisions that have not been made.

**Status:** Confirmed and deferred. Acknowledged structural heuristic instability.

---

### FM-167 — Dominance Scope Mismatch Between Per-Clause and Sentence-Scope Gate 10

**Trigger:** Hypothesized: per-clause Gate 10 computes dominance from in-clause non-negated beliefs; sentence-scope Gate 10 computes dominance from sentence-wide non-negated beliefs. The two scopes can disagree on what counts as dominant.

**System behavior:** No concrete adversarial input has triggered a divergence in confirmed tests. The idempotence guard (`eb.value == dom`) in the sentence-scope pass prevents double-flipping of beliefs already touched by per-clause Gate 10, which masks most disagreement cases.

**Why it fails:** The two passes are not formally reconciled. Their dominance computations are independent.

**Fix:** Possible direction: compute dominance once at sentence scope and pass it down to per-clause Gate 10. Or: require sentence-scope pass to skip beliefs already touched at per-clause scope. Neither implemented.

**Status:** Hypothesized, not confirmed by adversarial test. Held.

---

### FM-168 — "Only \<word\>" Restriction Capture Collision

**Trigger:** Hypothesized: "I like X-meetings and Y-meetings, but only X meetings on Z" — Gate 9's "only \<word\>" capture might match "meetings" (the shared entity token), then falsely treat both X-meetings and Y-meetings as restricted.

**System behavior:** In Phase 3 B8, the test input was "only meetings in the morning" with traits `team_meeting_preference` and `client_meeting_preference`. Gate 9 captured restriction token `meetings` (plural), but trait tokens are singular (`meeting`). Token-set intersection was empty. The collision was avoided by accidental pluralization mismatch, not by design.

**Why it fails:** "only \<word\>" pattern doesn't disambiguate between context-modifier and entity-token. If trait pluralization ever aligns with restriction-capture pluralization, the false-restriction case becomes active.

**Fix:** Possible direction: restrict the "only" capture to recognized entity nouns (not in `CONTEXT_WORDS_IN_TRAIT`) and require the captured word to be present in exactly one trait's tokens. Not implemented.

**Status:** Hypothesized; latent bug masked by an accident. Held with explicit awareness.

---

### FM-169 — Normalization Map Shadowing

**Trigger:** Phase 3 B9. `normalize_context("monday mornings")` returns `"morning"` because the dict iteration matches `mornings` → `morning` before reaching `monday mornings` → `monday_morning`. Specific compound contexts collapse to atomic ones.

**System behavior:** The negated context extracted from "not on Monday mornings" becomes `"morning"`, but the stored belief is at `"monday_morning"`. Token-set equality fails. No flip. The user's negation intent is silently lost.

**Why it fails:** `normalize_context()` iterates the normalization dict and returns on first substring match. Key ordering is the only thing protecting against false collapse. Shorter keys shadow longer keys.

**Fix direction:** Match longest key first (sort by length descending), or remove substring matching entirely and require exact-string keys. Not implemented.

**Status:** Confirmed and deferred. Next-priority fix per Commander V's directive after FM-170.

---

### FM-170 — Strict Reject Discards Legitimate Input

**Trigger:** Phase 3 B7. "I like Monday meetings and Tuesday meetings, but only Monday meetings in the morning." LLM produces `monday_meeting_preference` for the "only Monday meetings in the morning" clause with `context=morning`. Gate 7 detected trait drift AND saw a non-empty LLM context → strict reject path → entire belief discarded. The user's morning restriction is silently lost.

**System behavior:** "Only Monday meetings in the morning" produced no belief at all in v0.24. The user said something explicit; the system erased it.

**Why it fails:** The strict reject was correct in isolation (no fabrication), but applied too aggressively to legitimate compound input where both signals (trait-embedded day, separate LLM-supplied time) were explicit user statements.

**Fix:** v0.25 Gate 7 Path B — canonical compound repair. When trait drift is detected AND LLM context is non-empty, follow strict pipeline:
1. Normalize drift word independently: `normalize_context(drift_word)`
2. Normalize LLM context independently: `normalize_context(llm_context)`
3. Compose with underscore: `f"{drift_norm}_{llm_norm}"`
4. Validate against `CANONICAL_COMPOUND_CONTEXTS` (derived from `CONTEXT_NORMALIZATIONS.values()` containing underscore)
5. If canonical → repair to `(entity_preference, composed_context)`. Otherwise → reject.

The composed string is **never re-normalized**, because that would reintroduce FM-169 substring shadowing inside the FM-170 fix. The map is the authority on canonical compounds; if the composition isn't recognized, the system refuses to fabricate it.

Acknowledged costs: composition is order-sensitive (`drift_norm + "_" + llm_norm` only). Coverage is bounded by the canonical set (currently 6 entries: `after_lunch`, `before_bed`, `monday_morning`, `wife_cooks`, `with_family`, `with_friends`).

**Status:** Confirmed and fixed.

---

### FM-171 — Asymmetric Trait-Level Dominance in Sentence-Scope

**Trigger:** Phase 3 B5. "I like coffee in the morning and tea at night, but not coffee at night and not tea in the morning." Per-trait dominance treats coffee and tea independently. Coffee has a non-negated context (`morning`) → dominant established → coffee@night flips correctly. Tea has all contexts in the negated set (`night` and `morning` both negated) → dominant undetermined → tea@morning never flips.

**System behavior:** Same sentence structure for two traits, different correction outcome. Coffee gets fixed by sentence-pass; tea does not. The asymmetry is invisible to the user.

**Why it fails:** Per-trait dominance is structurally undetermined when all of a trait's beliefs land in negated contexts. The correction asymmetry surfaces only when looking across traits.

**Fix direction:** Possible policies: (a) when dominance is undetermined, default to "flip" (assume user is asserting the negation); (b) refuse to flip and surface ambiguity to the user. Both require policy decisions not yet made. Representation change may also help (per-context polarity).

**Status:** Confirmed and deferred. Same priority as FM-166 — both are structural heuristic limits.

---

### FM-172 — Extracted-List Duplicates Pre-Graph

**Trigger:** Phase 3 B3, B11. Same `(trait, context)` produced by multiple clauses, or by per-clause Gate 10 + sentence-scope Gate 10 both touching the same belief. `extract()` emits a list of `ExtractedBelief` objects with duplicates.

**System behavior:** `KnowledgeGraph.upsert_belief()` deduplicates on `(trait, namespace, context)`, so the final graph state is correct. But the list returned by `extract()` is not idempotent — its consumer sees duplicates.

**Why it fails:** Sentence-scope Gate 10 returns a parallel list to its input; per-clause beliefs that already exist at the same `(trait, context)` are not deduplicated against subsequent additions.

**Fix direction:** Deduplicate `results` in `extract()` before returning. Last-write wins on `(trait, context)`. One-line fix. Not yet applied.

**Status:** Confirmed and deferred. Low severity (masked by graph dedup at upsert). Held for cleanup pass.

---

## Structural Properties

These are not failure modes. They are permanent properties of the current architecture, named explicitly so that future work does not mistake them for bugs.

### SP-1 — Determinism Conditional on LLM Coverage

The deterministic gates govern which raw beliefs become final beliefs. They cannot govern which raw beliefs the LLM produces. A negation, restriction, or correction that targets a belief the LLM never materialized cannot be applied by any gate.

This is the boundary between extraction (LLM, stochastic) and validation (gates, deterministic). The system is not "fully deterministic" — it is "deterministic over a stochastic source."

Confirmed by Phase 3 B4 (faithful-LLM-forgets-negation) and B10b (no extrapolation).

### SP-2 — Pessimistic-LLM Hypothesis Unvalidated

The FM-163 fix corrects beliefs that the LLM extrapolates with wrong polarity into a separated negation clause. Whether `gpt-5.4-mini` actually produces those extrapolated beliefs in production is unverified at the time of this writing.

If the LLM faithfully returns `[]` for isolated "not at X" clauses, the fix has no inputs to correct, and the negation intent is silently lost (SP-1).

A live API run is required to determine which case occurs in practice.

Confirmed by Phase 3 B10 — both LLM paths produce different final states for the identical input.


## FM Register Status

```
FM-01 to FM-92:   all addressed in code
FM-93:            addressed
FM-94 to FM-108:  all addressed (FM-96 downgraded — single scripted instance)
FM-109 to FM-115: all addressed
FM-116 to FM-121: all addressed
FM-122 to FM-146: numbering gap (skipped during v0.21 sequence test assignment;
                   not reserved, not failure modes — these numbers are simply
                   unused due to a numbering error preserved for stability of
                   existing references in code and commits)
FM-147 to FM-152: v0.21 sequence tests — all addressed in v0.22
FM-153 to FM-157: v0.22 build — all addressed
FM-158:           hypothesized, held (no concrete failing input)
FM-159:           confirmed, deferred (representation work)
FM-160 / FM-163:  same issue, fixed in v0.24 (sentence-scope Gate 10)
FM-161 / FM-165:  same issue, fixed in v0.24 (token-set retrieval)
FM-162:           confirmed, deferred (canonicalization scope)
FM-164:           hypothesized as structural limit (genuine ambiguity)
FM-166:           confirmed, deferred (heuristic dominance)
FM-167:           hypothesized, held
FM-168:           hypothesized, held (latent, masked by accident)
FM-169:           confirmed, deferred (next-priority fix)
FM-170:           confirmed, fixed in v0.25 (canonical compound repair)
FM-171:           confirmed, deferred (representation)
FM-172:           confirmed, deferred (low severity)

SP-1, SP-2:       structural properties, not failure modes

Active critical FMs: none
Next open number: FM-173+
Numbering policy: gaps are not backfilled. FM-122 through FM-146 and
FM-158 through FM-162 remain permanently empty.
```

---

*The register is never closed. Axiom IX: Remain Permanently Breakable.*

---