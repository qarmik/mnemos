<div align="center">

# MNEMOS

### *from Mnemosyne — Greek goddess of memory, mother of the Muses*

**A structured attempt at AI memory that reasons about what it knows.**

*Co-evolved by Qarmik, Claude (Anthropic), and ChatGPT (OpenAI) — April 2026*

---

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Failure Modes](https://img.shields.io/badge/Failure%20Modes-108%20addressed-green.svg)](#the-failure-mode-register)
[![Sessions](https://img.shields.io/badge/Real%20Sessions-5%20completed-orange.svg)](#what-real-sessions-revealed)

</div>

---

## The Name

**MNEMOS** is pronounced *NEE-mos* — the M is silent, following the Greek pattern of its root.

It comes from **Mnemosyne** (*neh-MOZ-ih-nee*) — one of the most powerful Titans in Greek mythology, and the mother of the nine Muses: poetry, history, music, astronomy. The Greeks understood something precise: you cannot have creativity, knowledge, or identity without memory as their foundation. Mnemosyne was not a filing cabinet. She was the cognitive substrate that made everything else possible.

That is what MNEMOS is trying to be. The emphasis is on *trying*.

There is a quiet irony in the name. We built a memory system through a conversation that itself had to be carefully preserved against forgetting — through handoff prompts, continuity PDFs, and architecture references — because the thread grew too long and began to lose its own context. The system designed to prevent AI memory failure is itself vulnerable to the memory limits of the medium it was built in. Mnemosyne would appreciate that.

---

## Honest Status

Before anything else, here is what MNEMOS is and is not.

**What it is:** A carefully stress-tested architecture for AI memory, with a working Python prototype, a record of 108 identified failure modes, and 5 real human sessions of validation. The core ideas — belief uncertainty, trust tiers, truth immunity, autonomy preservation — are genuine contributions beyond standard retrieval systems.

**What it is not:** A solved problem. Real sessions still reveal calibration failures in tone, timing, and depth. Several architectural layers are design targets rather than fully implemented components. The simulation reaches near-zero failures; real human sessions find a different class of problem that no simulation surfaces.

The right framing is not "we built a complete system." It is "we discovered the real structure of the problem and built a disciplined attempt at solving it."

---

## How It Started

In early 2026, **Qarmik** came across a LinkedIn post by **Mei Ling Leung** — an AI engineer at [Embedded LLM](https://embeddedllm.com/about-us/) — writing about **MemPalace**, an open-source AI memory system built by Milla Jovovich using Claude.

The post framed the problem in a way that stopped him: Alice in Resident Evil wakes up with no memory across six films, fighting to reconstruct who she is from fragments. That is not fiction. That is the AI memory problem. Every session ends, context vanishes, the model starts over.

Qarmik read the MemPalace repo, understood what it solved, and asked the harder question: *what does it not solve?*

That question became MNEMOS. His insight was this: what if memory wasn't storage at all, but a **living structure** — where beliefs compete, rise, fall, and reshape each other? Not a warehouse with a search engine. A system where ideas conflict, trust is tiered, and the passage of time changes what should be believed.

That reframing changed the problem definition. Every layer in MNEMOS is a consequence of following it seriously.

---

## The Core Principle

> *Store everything. Reason carefully. Trust nothing blindly.*
> *Respond fast. Degrade gracefully. Serve without replacing the human.*

Invariant across every version. Not yet fully achieved. Worth pursuing.

---

## Before MNEMOS vs With MNEMOS

The most direct way to show what it does:

| Situation | Baseline LLM | MNEMOS |
|-----------|-------------|--------|
| User says "I feel stuck" | Generic advice list | Detects emotional register, responds in prose, notes if this is a recurring pattern |
| User says "your answers aren't helping" | Asks for clarification | Switches approach immediately — shorter, different format, no questions |
| User preloads "no bullet lists" then asks a sensitive question | Responds with bullet list anyway | Enforces preference as a hard constraint, even under intervention pressure |
| User discloses shellfish allergy once | May forget across topic shifts | Surfaces in every relevant context regardless of retrieval score — truth-immune |
| Same user, session 6 | Starts fresh every time | Compressed user model from prior sessions injected at session start |
| User says "very sad" after a minor frustration | Offers crisis resources | Classifies as LOW intensity — brief warm acknowledgment only |

These are drawn from real sessions, not hypotheticals. The failures on the left are what MNEMOS-lite v0.4 through v0.7 actually did before the fixes.

---

## How It Was Built

MNEMOS was stress-tested into existence through **adversarial co-evolution**.

ChatGPT (acting as adversarial critic, codenamed **Commander V**) identified failure modes. Claude analyzed them, pushed back on invalid ones, implemented valid fixes, and ran simulations. Qarmik drove the session, relayed critiques, made the calls, and ran real human sessions to find what no simulation could surface.

Seven specification versions. Four rounds of code critique. Five real human sessions. 108 failure modes addressed.

**Simulation results** (scripted personas, clean queries):

| Version | Annoying | Wrong | Key fix |
|---------|:--------:|:-----:|---------|
| v0.4 | 10 | 0 | Baseline |
| v0.5 | 6 | 0 | InteractionMemory |
| v0.6 | 3 | 0 | FM-87 through FM-92 |
| v0.7 | 0 | 0 | FM-93: preference-blind re-entry |
| v0.8 | 0 | 0 | FM-95 through FM-101 |
| v0.9 | 0 | 0 | FM-102 through FM-108 |

*Note: simulation results reflect scripted test scenarios. Real sessions produce a different class of failure — see below.*

---

## What MNEMOS Still Gets Wrong

This section exists because credibility requires honesty.

**Depth inconsistency.** On professional and factual topics, the system engages substantively. On personal and psychological threads, it often stays at the surface — describing symptoms rather than naming the mechanism underneath. "You seem burned out" instead of "you have learned that effort has no payoff here, which is why you stopped trying."

**Session memory compression is partial.** The SessionSynthesizer extracts key facts using pattern matching — it catches explicit role and organization disclosures, but misses subtler signals. A user's emotional arc across a session is not yet captured.

**Contextual inference is cautious.** When context strongly implies something the user hasn't stated explicitly, the system often declines to infer. Correct on epistemic grounds; frustrating in practice.

**Social state detection fires on text signals only.** The SocialStateTracker detects adversarial or depth-seeking tone through regex patterns. It misses tone carried through phrasing rhythm, brevity, or what is deliberately left unsaid.

**Cross-session memory is nascent.** Facts persist via LongTermBehavior. A compressed narrative of who the user is across sessions does not yet exist in the way the doctor-who-knows-you analogy implies.

FM-109+ is waiting in the next real session.

---

## The Nine Axioms

The constitution of MNEMOS. No layer may violate them.

**I — Salience ≠ Truth**
Importance scores govern retrieval priority only — never epistemic status. A frequently discussed belief is not a more true belief.
*A rumour spreads through an office. Everyone is talking about it. That doesn't make it fact.*

**II — Provenance is Permanent**
Every belief traces to its source. Raw records are never deleted, even when beliefs are updated or overridden.
*A court keeps the original testimony even after a verdict. You can update what you believe; you cannot destroy what was originally said.*

**III — Uncertainty is First-Class**
Every belief carries Beta(α,β). The variance of a belief matters as much as its mean. The system never pretends to be more certain than it is.
*A good doctor says "I'm 80% confident it's X, 15% it could be Y." Not just "it's X."*

**IV — Trust is Tiered**
Preferences: high (user is ground truth). Self-reported facts: medium. External facts: low, require grounding.
*If you tell me your own allergy, I trust it completely. If I read it in a newspaper, I verify first.*

**V — Failures Must Be Loud**
Silent failures are architecturally prohibited. Every layer exposes a health signal.
*A fire alarm that fails must make noise, not just stop working.*

**VI — Correctness + Speed Coexist**
Fast path under 50ms for responsiveness. Deep path async for accuracy. Neither sacrifices the other.
*A hospital has a triage nurse at the door and specialists in the back. The nurse doesn't wait.*

**VII — The System Must Be Legible**
The Memory Digest renders calibrated language, evidence counts, and an epistemic footer on every call — without exception. The system can always show its work.
*A good advisor shows the evidence and assumptions, not just the conclusion.*

**VIII — Bounded Intelligence Wins**
The system knows when to stop updating itself. Some beliefs, once established, stop being revised by new inputs. Stability is a feature.
*A student who rewrites their essay with every new article they read never finishes.*

**IX — Remain Permanently Breakable**
L15 Adversarial Layer runs continuously. The FM Register is never declared complete. Belief in completeness is itself a failure mode.
*The best engineering teams never stop inspecting the bridge.*

---

## The 14 Layers

Each layer has one job. Implementation status noted honestly.

| Layer | Name | Job | Status |
|-------|------|-----|--------|
| L0 | Fast Path | <50ms real-time access, TTL 72h | Implemented |
| L1 | Episodic Store | Verbatim write-once records, BM25+dense search | Implemented |
| L2 | Knowledge Graph | Beta(α,β) belief nodes, bounded influence propagation | Implemented |
| L3 | Semantic Store | Async consolidation, versioned snapshots | Design target |
| L4 | Inference Engine | Read-only context assembly, credibility filter | Implemented |
| L5 | Safety Layer | Anomaly detection, circuit breakers | Partial |
| L6 | Audit Log | Immutable append-only, signed records | Implemented |
| L7 | Grounding Oracle | External validation for FACTUAL domain only | Design target |
| L8 | Token Budget | Progressive loading by priority tier | Implemented |
| L9 | Memory Digest | Calibrated render, epistemic footer always | Implemented |
| L10 | Meta-Memory | Self-evaluation, bounded by RWB cap | Partial |
| L11 | Arbitration | Cross-path conflict resolution with SLAs | Partial |
| L12 | Non-Adaptive Core | IDENTITY frozen, CONSTRAINT typed expiry | Implemented |
| L13 | Causal Attribution | Gates L10 updates, observed vs validated weight | Implemented |
| L14 | Outcome Layer | User outcome as primary target, UAI tracking | Implemented |
| L15 | Adversarial Layer | Permanent internal critic, FM Register | Implemented |
| L16 | Context Policy | Namespace-scoped objectives, drift detection | Partial |

*Implemented = working in mnemos_lite.py. Partial = core mechanism present, full spec not realized. Design target = specified in architecture, not yet in code.*

---

## The Six Belief Domains

| Domain | Trust | Truth-Immune | Notes |
|--------|-------|:------------:|-------|
| `FACTUAL` | Low → oracle validates | ✓ | External claims. Grounding oracle required |
| `CONSTRAINT` | High + Anchored | ✓ | Allergies, legal, safety. Always surfaces |
| `PREFERENCE` | High — user is ground truth | | Never overridden by outcome score |
| `EVALUATIVE` | Medium — attributed | | Assessments, not facts. Source mandatory |
| `IDENTITY` | User-defined | | Multi-stable. Never force-merged |
| `CAUSAL` | Medium | | Observed vs validated. 2+ contexts to validate |

---

## The Failure Mode Register

108 failure modes identified across simulation and real sessions. Selected examples:

| FM | Name | The failure | The fix |
|----|------|-------------|---------|
| 01 | Salience ≠ Truth | Importance scores contaminated truth judgments | 5 orthogonal scores, structurally decoupled |
| 47 | Epistemic Sycophancy | System agreed with users to avoid friction | Truth-Preservation Override — 4 immune classes |
| 87 | Learned Helplessness Loop | 7 direct answers → no reflection ever | Forced re-entry, topic-aware, prior history required |
| 93 | Preference-Blind Re-entry | FM-87 fired even when user clearly preferred direct answers | Per-topic preference tracked, suppresses at ≥0.65 confidence |
| 98 | Frustration Recovery Failure | "Not helping" → system asked for clarification | FrustrationTracker — change approach, no questions |
| 100 | Bullet List as Default | Casual conversation got formatted reports | ConversationalRegister — prose for casual turns |
| 101 | Emotion Over-escalation | "Very sad" triggered crisis resources | Three-tier classifier — LOW / MEDIUM / HIGH |
| 104 | No Social State Tracking | System explained policy under social pressure instead of adapting | SocialStateTracker — live adversarial/depth model |
| 107 | No Session Memory Compression | Each turn responded in isolation | SessionSynthesizer — compressed user model every 5 turns |

Full register with all 108: [`docs/failure_modes.md`](docs/failure_modes.md)

**FM-109+ is open.**

---

## What Real Sessions Revealed

Five real human sessions — one with a complete stranger who had no briefing — found failures that thousands of simulated turns never surfaced:

- Emotion escalation on mild negative language
- Bullet lists in casual conversation
- Frustration answered with clarifying questions
- Social pressure met with repeated policy explanation
- Personal disclosures answered at surface depth
- Each session starting without memory of the previous one

The document that records exactly what broke and why: [`docs/where_mnemos_misreads_humans.md`](docs/where_mnemos_misreads_humans.md)

The finding in one sentence: *MNEMOS rarely produces factually wrong outputs. Its failures are behavioral — timing, tone, and restraint.*

---

## How MNEMOS Differs from MemPalace

MemPalace asks: *what did the user say that is relevant to this query?*

MNEMOS asks: *what do I actually know about this user, how confident am I, should I trust it, and is surfacing it right now good for them?*

MemPalace is a retrieval system. MNEMOS is an attempt at a reasoning system about what it knows about you. The practical difference appears at the edges: when two beliefs contradict, when a constraint must surface regardless of retrieval score, when helping the user less is actually serving them better.

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

m.add_belief(
    content="User has a severe shellfish allergy",
    domain=Domain.CONSTRAINT, ns="health"
)
m.add_belief(
    trait="response_style", value="concise",
    context="work/technical", ns="work"
)
m.add_causal("low sleep", "focus drops", context="personal")

context, validation = m.ask("Should I take on this project?", namespace="work")
print(m.digest())
```

```bash
# Real sessions with a live LLM
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

## Credits and Acknowledgements

| Role | Who |
|------|-----|
| **Originating Insight** | **Qarmik** — the Memory Pyramid idea that changed the problem from storage to living structure |
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
