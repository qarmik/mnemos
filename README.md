<div align="center">

# MNEMOS

### *from Mnemosyne — Greek goddess of memory, mother of the Muses*

**A structured attempt at AI memory that reasons about what it knows.**

*Co-evolved by Qarmik, Claude (Anthropic), and ChatGPT (OpenAI) — April 2026*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Failure Modes](https://img.shields.io/badge/Failure%20Modes-108%20addressed-green.svg)](#the-failure-mode-register)
[![Real Sessions](https://img.shields.io/badge/Real%20Sessions-5%20completed-orange.svg)](#what-real-sessions-revealed)

</div>

---

Most AI systems remember poorly.

They retrieve what was said. They do not reason about what they *know* — how confident, how recent, whether it contradicts something else, whether surfacing it right now is actually good for the user.

MNEMOS is a structured attempt to fix that.

*This project is for engineers and researchers exploring how AI should behave across sessions — not just respond within one.*

---

## The Name

**MNEMOS** (*NEE-mos* — the M is silent) comes from **Mnemosyne** (*neh-MOZ-ih-nee*), the Greek Titan who personified memory itself and was the mother of the nine Muses. The Greeks understood something precise: you cannot have creativity, knowledge, or identity without memory as their foundation. She was not a filing cabinet. She was the cognitive substrate that made everything else possible.

That is what MNEMOS is trying to be. The emphasis is on *trying*.

There is a quiet irony in the name. We built a memory system through a conversation that itself had to be carefully preserved against forgetting — through handoff prompts and continuity documents — because the thread grew too long and began to lose its own context. The system designed to prevent AI memory failure is itself vulnerable to the memory limits of the medium it was built in.

---

## Honest Status

**What it is:** A carefully stress-tested architecture with a working Python prototype, 108 identified failure modes, and 5 real human sessions of validation. The core ideas — belief uncertainty, trust tiers, truth immunity, autonomy preservation — are genuine contributions beyond standard retrieval systems.

**What it is not:** A solved problem. Real sessions still reveal calibration failures in tone, timing, and depth. Several layers are design targets rather than fully implemented components. Simulation reaches near-zero failures; real humans find a different class of problem entirely.

The right framing: *"We discovered the real structure of the problem and built a disciplined attempt at solving it."*

---

## A Real Failure (Why MNEMOS Exists)

Early in testing, a user said *"I feel stuck"* mid-session.

The system gave a seven-point bullet list: set goals, seek feedback, update your LinkedIn, network with three people this week.

The user disengaged. The list was not wrong. It was completely tone-deaf. The user had just disclosed something personal and real. They did not need a productivity framework. They needed acknowledgment.

This became FM-98 through FM-101 — a cluster of failures around emotional register, frustration recovery, and conversational tone. The fixes: a three-tier emotion classifier, a frustration tracker that changes approach immediately instead of asking clarifying questions, and a conversational register detector that suppresses structured formatting when the user is just talking.

In sessions after those fixes: frustration-triggered clarification requests dropped to near zero. Preference violations (like bullet lists after a user said "no bullet lists") were eliminated in the session runner. Emotional over-escalation — crisis resources for mild disappointment — stopped occurring.

That pattern repeated 108 times. A failure observed, named, fixed, measured. That is the method.

---

## What Actually Changes in Practice

| Situation | Typical LLM | MNEMOS |
|-----------|-------------|--------|
| User says "I feel stuck" | Generic advice list | Recognizes emotional context, responds in prose, notes if it is a recurring pattern |
| User says "your answers aren't helping" | Asks for clarification | Switches approach immediately — shorter, different format, no questions |
| User preloads "no bullet lists" | Responds with bullets anyway | Enforces preference as a hard constraint, even under intervention pressure |
| User discloses shellfish allergy once | May lose it across topic shifts | Surfaces in every relevant context regardless of retrieval score — truth-immune |
| Same user, session 6 | Starts completely fresh | Compressed user model from prior sessions injected at session start |
| User says "very sad" after minor frustration | Offers crisis resources | Classifies as LOW intensity — brief warm acknowledgment only |

These are drawn from real sessions, not hypotheticals. The left column is what MNEMOS-lite v0.4 actually did.

---

## How It Started

In early 2026, **Qarmik** read a LinkedIn post by **Mei Ling Leung** — AI engineer at [Embedded LLM](https://embeddedllm.com/about-us/) — about **MemPalace**, an open-source memory system built by Milla Jovovich using Claude.

The post framed the problem cleanly: Alice in Resident Evil wakes up with no memory across six films, fighting to reconstruct who she is from fragments. That is the AI memory problem. Every session ends, context vanishes, the model starts over.

Qarmik read the MemPalace repo, understood what it solved, and asked: *what does it not solve?*

His answer: MemPalace retrieves what was said. It does not reason about what is known — how confident, how trusted, when a belief should expire, whether helping the user more is actually making them less capable. What if memory were a living structure where beliefs compete, rise, fall, and reshape each other? Not storage. A system with judgment.

That question became MNEMOS.

---

## The Core Principle

> *Store everything. Reason carefully. Trust nothing blindly.*
> *Respond fast. Degrade gracefully. Serve without replacing the human.*

Invariant across every version.

---

## How It Was Built

Adversarial co-evolution across seven specification versions, four code critique rounds, and five real human sessions.

ChatGPT (codenamed **Commander V**) identified failure modes. Claude analyzed, pushed back on invalid ones, implemented valid fixes, ran simulations. Qarmik drove, relayed critiques, made the calls, and ran real sessions to find what simulation could not surface.

**Simulation results** *(scripted personas — real sessions produce different failures, see below)*:

| Version | Annoying | Wrong | Key fix |
|---------|:--------:|:-----:|---------|
| v0.4 | 10 | 0 | Baseline |
| v0.5 | 6 | 0 | InteractionMemory |
| v0.6 | 3 | 0 | FM-87 through FM-92 |
| v0.7 | 0 | 0 | FM-93: preference-blind re-entry |
| v0.8 | 0 | 0 | FM-95 through FM-101: real-session calibration |
| v0.9 | 0 | 0 | FM-102 through FM-108: social intelligence layer |

---

## What MNEMOS Still Gets Wrong

Most failures are not about knowledge. They are about timing, tone, and restraint.

**Depth inconsistency.** On professional topics, the system engages substantively. On personal threads, it often stays at the surface — describing symptoms rather than mechanisms. "You seem burned out" instead of "you have learned that effort has no payoff here, which is why you stopped trying."

**Session memory compression is partial.** The SessionSynthesizer catches explicit disclosures. A user's emotional arc across a session is not yet captured.

**Cautious inference.** When context strongly implies something unstated, the system often declines to infer. Epistemically correct; practically frustrating.

**Social detection is text-only.** The SocialStateTracker reads tone through patterns. It misses tone carried through brevity, rhythm, or deliberate omission.

**Cross-session memory is nascent.** Facts persist. A narrative of who the user is across sessions does not yet exist the way the architecture intends.

FM-109+ is waiting in the next real session.

---

## The Nine Axioms

The constitution of MNEMOS. No layer may violate them.

| # | Axiom | What it means |
|---|-------|---------------|
| I | Salience ≠ Truth | Importance governs retrieval priority only — never epistemic status |
| II | Provenance is Permanent | Every belief traces to source. Raw records never deleted |
| III | Uncertainty is First-Class | Every belief carries Beta(α,β). Variance matters as much as mean |
| IV | Trust is Tiered | Preferences: high. Self-reported facts: medium. External: low |
| V | Failures Must Be Loud | Silent failures architecturally prohibited. Every layer exposes health signal |
| VI | Correctness + Speed Coexist | Fast path <50ms. Deep path async. Neither sacrifices the other |
| VII | The System Must Be Legible | Memory Digest with calibrated language and epistemic footer — always |
| VIII | Bounded Intelligence Wins | Non-Adaptive Core + convergence criterion. The system knows when to stop |
| IX | Remain Permanently Breakable | L15 always active. FM Register never closed. Completeness is a failure mode |

---

## The 14 Layers

*MNEMOS is layered for clarity, but not all layers are equally mature. For current behavior, focus on L0–L4, L9, L12–L15.*

| Layer | Name | Job | Status |
|-------|------|-----|--------|
| L0 | Fast Path | <50ms real-time access, TTL 72h | Implemented |
| L1 | Episodic Store | Verbatim write-once records, BM25+dense search | Implemented |
| L2 | Knowledge Graph | Beta(α,β) nodes, bounded influence propagation | Implemented |
| L3 | Semantic Store | Async consolidation, versioned snapshots | Design target |
| L4 | Inference Engine | Read-only context assembly, credibility filter | Implemented |
| L5 | Safety Layer | Anomaly detection, circuit breakers | Partial |
| L6 | Audit Log | Immutable append-only, signed records | Implemented |
| L7 | Grounding Oracle | External validation, FACTUAL domain only | Design target |
| L8 | Token Budget | Progressive loading by priority tier | Implemented |
| L9 | Memory Digest | Calibrated render, epistemic footer always | Implemented |
| L10 | Meta-Memory | Self-evaluation, bounded by RWB cap | Partial |
| L11 | Arbitration | Cross-path conflict resolution with SLAs | Partial |
| L12 | Non-Adaptive Core | IDENTITY frozen, CONSTRAINT typed expiry | Implemented |
| L13 | Causal Attribution | Gates L10 updates, observed vs validated weight | Implemented |
| L14 | Outcome Layer | User outcome primary target, UAI tracking | Implemented |
| L15 | Adversarial Layer | Permanent internal critic, FM Register | Implemented |
| L16 | Context Policy | Namespace-scoped objectives, drift detection | Partial |

---

## The Six Belief Domains

| Domain | Trust | Truth-Immune | Notes |
|--------|-------|:------------:|-------|
| `FACTUAL` | Low → oracle validates | ✓ | External claims. Grounding required |
| `CONSTRAINT` | High + Anchored | ✓ | Allergies, legal, safety. Always surfaces |
| `PREFERENCE` | High — user is ground truth | | Never overridden by outcome score |
| `EVALUATIVE` | Medium — attributed | | Assessments, not facts. Source mandatory |
| `IDENTITY` | User-defined | | Multi-stable. Never force-merged |
| `CAUSAL` | Medium | | Observed vs validated. 2+ contexts required |

---

## The Failure Mode Register

108 failure modes identified across simulation and real sessions. Selected:

| FM | Name | The failure | The fix |
|----|------|-------------|---------|
| 01 | Salience ≠ Truth | Importance contaminated truth judgments | 5 orthogonal scores, structurally decoupled |
| 47 | Epistemic Sycophancy | System agreed to avoid friction | Truth-Preservation Override |
| 87 | Learned Helplessness Loop | 7 direct answers → no reflection ever | Forced re-entry, topic-aware |
| 93 | Preference-Blind Re-entry | FM-87 fired despite user preference for direct answers | Per-topic preference tracked, suppresses at ≥0.65 confidence |
| 98 | Frustration Recovery | "Not helping" → asked for clarification | FrustrationTracker — change approach, no questions |
| 100 | Bullet List Default | Casual conversation got formatted reports | ConversationalRegister — prose for casual turns |
| 101 | Emotion Over-escalation | "Very sad" triggered crisis resources | Three-tier classifier: LOW / MEDIUM / HIGH |
| 104 | No Social State | System explained policy under pressure instead of adapting | SocialStateTracker — live adversarial/depth model |
| 107 | No Session Compression | Each turn in isolation | SessionSynthesizer — compressed user model every 5 turns |

Full register: [`docs/failure_modes.md`](docs/failure_modes.md)

**FM-109+ is open.**

---

## What Real Sessions Revealed

Five real human sessions — including one with a complete stranger who had no briefing — found failures that thousands of simulated turns never surfaced. The document recording exactly what broke, why, and what it means: [`docs/where_mnemos_misreads_humans.md`](docs/where_mnemos_misreads_humans.md)

*Simulation finds annoying failures. Real humans find a different class entirely — failures that require genuine ambiguity, emotional subtext, and unpredictable intent to trigger.*

---

## How MNEMOS Differs from MemPalace

MemPalace asks: *what did the user say that is relevant to this query?*

MNEMOS asks: *what do I actually know about this user, how confident am I, should I trust it, and is surfacing it right now good for them?*

MemPalace is a retrieval system with impressive benchmark results. MNEMOS is an attempt at a reasoning system about what it knows about you. The difference appears at the edges — contradicting beliefs, truth-immune constraints, and the question of whether more help is actually less.

---

## Quick Start

```bash
pip install chromadb sentence-transformers rank-bm25  # optional
pip install openai                                     # for real sessions
```

```python
from mnemos_lite import MnemosLite, Domain

m = MnemosLite()
m.new_session()

m.add_belief(content="User has a severe shellfish allergy",
             domain=Domain.CONSTRAINT, ns="health")
m.add_belief(trait="response_style", value="concise",
             context="work/technical", ns="work")
m.add_causal("low sleep", "focus drops", context="personal")

context, validation = m.ask("Should I take on this project?", namespace="work")
print(m.digest())
```

```bash
export OPENAI_API_KEY="your_key"
python mnemos_session.py
```

---

## Repo Structure

```
mnemos/
├── mnemos_lite.py                         Core prototype — v0.9, ~1900 lines
├── mnemos_session.py                      Real session runner (OpenAI API)
├── MNEMOS_Architecture_Reference.pdf      Complete continuity document
└── docs/
    ├── architecture.md                    Full specification
    ├── failure_modes.md                   All 108 FMs
    ├── simulation.md                      v0.4 through v0.9 results
    └── where_mnemos_misreads_humans.md    Observations from real sessions
```

---

## Credits

| Role | Who |
|------|-----|
| **Originating Insight** | **Qarmik** — Memory Pyramid, changed the problem from storage to living structure |
| **Implementation and Co-design** | **Claude** (Anthropic) |
| **Adversarial Critic and Co-design** | **ChatGPT / Commander V** (OpenAI) |
| **Catalyst** | **Milla Jovovich** — MemPalace showed what was possible and what remained unsolved |
| **The spark** | **Mei Ling Leung**, AI Engineer at [Embedded LLM](https://embeddedllm.com/about-us/) |

MNEMOS began because Mei Ling wrote about MemPalace, Qarmik read it, and asked what it didn't solve. Two AI systems from competing companies, coordinated by a human who changed the question, built something neither would have reached alone.

---

## License

MIT. See [LICENSE](LICENSE).

---

<div align="center">

*"You cannot have the Muses — poetry, history, music, astronomy — without memory as their mother."*

*That is what MNEMOS is trying to be.*

</div>
