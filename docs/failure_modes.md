# MNEMOS Failure Mode Register

**FM-01 through FM-121 — all addressed**
*Last updated: v0.20 / Session 16 / April 2026*

The FM Register is the adversarial spine of MNEMOS. Every failure mode was identified, named, fixed, and measured before the next session ran. The register is never closed — FM-122 is waiting in the next real session.

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

## FM Register Status

```
FM-01 to FM-92:   all addressed in code
FM-93:            addressed
FM-94 to FM-108:  all addressed (FM-96 downgraded — single scripted instance)
FM-109 to FM-115: all addressed
FM-116 to FM-121: all addressed

Active critical FMs: none
FM-122+: open — requires real sessions to discover
```

---

*The register is never closed. Axiom IX: Remain Permanently Breakable.*
