<div align="center">

# MNEMOS

### *from Mnemosyne — Greek goddess of memory, mother of the Muses*

**An AI memory architecture built to serve humans without replacing them.**

*Co-evolved by Qarmik, Claude (Anthropic), and ChatGPT (OpenAI) — April 2026*

---

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Failure Modes](https://img.shields.io/badge/Failure%20Modes-108%20addressed-green.svg)](#the-failure-mode-register)
[![Sessions](https://img.shields.io/badge/Real%20Sessions-5%20completed-orange.svg)](#what-real-sessions-revealed)

</div>

---

## The Name

**MNEMOS** is pronounced *NEE-mos* — the M is silent, following the Greek pattern of its root word.

It comes from **Mnemosyne** (*neh-MOZ-ih-nee*) — one of the most important Titans in Greek mythology. She was the personification of memory itself, and the mother of the nine Muses: poetry, history, music, astronomy, and the rest. The Greeks understood something profound: you cannot have creativity, knowledge, or identity without memory as their foundation. Mnemosyne was not a filing cabinet. She was the cognitive substrate that made everything else possible.

That is exactly what MNEMOS is trying to be.

The name also nods to *mnemonics* — the techniques humans use to aid memory — and to the Greek root *mneme* (μνήμη), meaning memory or recollection.

There is a quiet irony in the name that feels appropriate for this project. We built a memory system through a conversation that itself had to be carefully preserved against forgetting — through handoff prompts, continuity PDFs, and architecture references — because the thread grew too long and began to lose its own context. The system designed to prevent AI memory failure is itself vulnerable to the memory limits of the medium it was designed in. Mnemosyne would appreciate that.

---

## How It Started

In early 2026, **Qarmik** came across a LinkedIn post by **Mei Ling Leung** — an AI engineer at [Embedded LLM](https://embeddedllm.com/about-us/) — writing about **MemPalace**, an open-source AI memory system built by Milla Jovovich using Claude.

The post made a simple observation that stopped him cold.

Alice in Resident Evil wakes up with no memory across six films, fighting to reconstruct who she is from fragments. That is not fiction. That is the AI memory problem. Every session ends, context vanishes, the model starts over. Umbrella Corporation is the session boundary.

Jovovich's answer with MemPalace was elegant: don't extract facts from conversations — store everything verbatim, organize it hierarchically, let structure do the filtering before the vector search fires. Impressive benchmark score. $0.70 a year to run.

Qarmik read the repo, understood what it solved, and then asked the harder question: *what does it not solve?*

That question became MNEMOS.

The insight he brought was this: what if memory wasn't storage at all, but a **living structure** — where beliefs compete, rise, fall, and reshape each other over time? Not a warehouse with a search engine. A political system where ideas compete, power shifts, conflicts get resolved, and history gets rewritten.

That single reframing changed everything. Every layer in MNEMOS is a consequence of following that idea to its conclusions.

---

## The Core Principle

> *Store everything. Reason carefully. Trust nothing blindly.*
> *Respond fast. Degrade gracefully. Serve without replacing the human.*

This principle is invariant. No version of MNEMOS has ever violated it. No future version will.

---

## How It Was Built

MNEMOS was stress-tested into existence through **adversarial co-evolution**.

ChatGPT (acting as adversarial critic, codenamed **Commander V**) identified failure modes. Claude analyzed them, pushed back on the invalid ones, implemented the valid fixes, and ran simulations. Qarmik drove the session, relayed critiques, made the calls, and ran real human sessions to find what no simulation could surface.

Seven specification versions. Four rounds of code critique. Five real human sessions. **108 failure modes** identified and addressed.

The simulation result that tells the story:

| Version | Annoying | Wrong | What changed |
|---------|:--------:|:-----:|--------------|
| v0.4 | 10 | 0 | Baseline — correct but felt like a nagging supervisor |
| v0.5 | 6 | 0 | InteractionMemory class |
| v0.6 | 3 | 0 | FM-87 through FM-92: re-entry, clustering, resistance |
| v0.7 | 0 | 0 | FM-93: preference-blind re-entry |
| v0.8 | 0 | 0 | FM-95 through FM-101: real-session calibration |
| v0.9 | 0 | 0 | FM-102 through FM-108: social intelligence layer |

The system has been **correct from the start**. Every failure was a calibration failure — wrong tone, wrong timing, wrong format, wrong intensity. Correctness is an engineering problem. Calibration is a human problem. The simulation solved the first. Real sessions revealed the second.

---

## The Nine Axioms

These are the constitution of MNEMOS. No layer may ever violate them.

---

**I — Salience ≠ Truth**

Just because something is talked about often doesn't make it true. Importance scores govern *retrieval priority* only — never epistemic status.

*A rumour spreads through an office. Everyone is talking about it. That doesn't make it fact. MNEMOS keeps importance and truth in completely separate boxes, permanently.*

---

**II — Provenance is Permanent**

Every belief must remember where it came from. The original record is never deleted, even when beliefs are updated or overridden.

*A court keeps the original testimony even after a verdict. You can update what you believe, but you can never destroy the evidence of what was originally said.*

---

**III — Uncertainty is First-Class**

Every belief carries a confidence score — not just what is believed, but how strongly, expressed as a Beta distribution (α, β). The variance of a belief matters as much as its mean.

*A good doctor doesn't say "you have condition X." They say "I'm 80% confident it's X, 15% it could be Y, let's test further." MNEMOS never pretends to be more certain than it actually is.*

---

**IV — Trust is Tiered**

Not all sources are equally trustworthy. Preferences: high (user is ground truth). Self-reported facts: medium. External facts: low, require grounding.

*If you tell me your own food allergy, I trust that completely. If a friend tells me, I trust it less. If I read it in a newspaper, I verify before acting. Three tiers, always.*

---

**V — Failures Must Be Loud**

Silent failures are architecturally prohibited. Every layer must expose a health signal. A system that fails quietly is more dangerous than one that fails noisily.

*A fire alarm that fails must make noise, not just stop working. If something goes wrong in MNEMOS, it surfaces visibly. Always.*

---

**VI — Correctness + Speed Coexist**

The system must be fast enough to use and accurate enough to trust. Neither sacrifices the other. Fast path under 50ms. Deep path async. Both running simultaneously.

*A hospital has a triage nurse at the door for fast initial decisions, and specialists in the back for thorough work. The nurse doesn't wait for the specialist before seeing you.*

---

**VII — The System Must Be Legible**

The system must always be able to explain what it knows, how confident it is, and why. The Memory Digest renders calibrated language, evidence counts, and an epistemic footer on every call — without exception.

*A good financial advisor doesn't just say "invest here." They say "based on these three pieces of evidence, with this level of confidence, here are my assumptions." MNEMOS always shows its work.*

---

**VIII — Bounded Intelligence Wins**

The system must know when to stop updating itself. Non-Adaptive Core + Stability Budget + convergence criterion. Some beliefs, once established, stop being updated by new inputs.

*A student who keeps rewriting their essay right up to submission, changing their mind with every new article they read, never produces good work. At some point you commit. Stability is a feature.*

---

**IX — Remain Permanently Breakable**

L15 Adversarial Layer runs continuously inside the system. The FM Register is never declared complete. Belief in completeness is the most dangerous failure mode of all.

*The best engineering teams never say "this bridge is perfect, no more inspections." They keep testing, keep looking for cracks. The failure register is open at FM-109 right now. It will never be closed.*

---

## The 14 Layers

Each layer has one job. None of them do each other's job.

---

**L0 — Fast Path** `<50ms · TTL 72h`

The reflex layer. Holds the most recent, most relevant information ready to fire instantly.

*When you touch a hot stove, your hand pulls back before your brain consciously registers pain. L0 is that reflex.*

---

**L1 — Episodic Store** `verbatim · write-once · never deleted`

The court stenographer. Every word spoken, exactly as said, forever. No interpretation. No summarization. When you need the original source, it is always there.

---

**L2 — Knowledge Graph** `Beta(α,β) nodes · bounded influence`

The detective's board. Not facts in isolation — a web of beliefs with confidence scores, showing how they connect and how the strength of one belief propagates to related beliefs.

---

**L3 — Semantic Store** `async consolidation · versioned snapshots`

Where raw records graduate into organized beliefs. The journalist's notes (L1) become the finished article (L3). The notes are preserved. The article is what gets used.

---

**L4 — Inference Engine** `read-only · intent-aware · never writes`

The barrister who reads all the case files before entering the courtroom. They don't change the files. They just know them cold and use them to construct the argument.

---

**L5 — Safety Layer** `anomaly detection · circuit breakers`

The compliance officer. Notices when something doesn't add up — unusual patterns, contradictions, attempts to manipulate. Trips circuit breakers before damage propagates.

---

**L6 — Audit Log** `immutable · append-only · signed`

The blockchain ledger. Once written, it cannot be altered. Every decision, every belief update, every failure mode logged — permanently and in order.

---

**L7 — Grounding Oracle** `FACTUAL domain only`

The fact-checker. Verifies external claims before they enter the belief system. Critically: only checks facts — never tells you what your preferences should be or whether your identity is correct.

---

**L8 — Token Budget** `Core 120T · Fast 80T · Essential 500T`

The barrister who can only bring a limited number of files into the courtroom. Most critical things first: safety constraints, identity, recent context. Lower-priority details wait outside.

---

**L9 — Memory Digest** `calibrated · evidence counts · epistemic footer always`

The patient summary before the appointment. One page. What we know, how confident we are, what's uncertain. The epistemic footer always reminds: confidence is not truth. User is ground truth on their own preferences.

---

**L10 — Meta-Memory** `bounded · epsilon-floor · outcome-gated`

The quality control inspector who checks not the product, but the production process. Evaluates whether the beliefs that exist are reliable and whether the system is learning well — bounded by hard caps to prevent infinite self-reflection.

---

**L11 — Arbitration Engine** `3 strategies · diversity budget · SLAs`

The judge where two credible witnesses give contradictory testimony. Doesn't ignore either. Applies a structured process — evidence weight, consistency, stakes — and reaches a reasoned resolution.

---

**L12 — Non-Adaptive Core** `IDENTITY: frozen · CONSTRAINT: typed expiry`

The constitution. Ordinary beliefs can be updated. But the foundational ones — your shellfish allergy, your core identity — cannot be overwritten because something in a session contradicted them. Some things require extraordinary evidence to change. Some things cannot change at all.

---

**L13 — Causal Attribution** `observed vs validated weight · 2+ contexts required`

The scientist who insists on understanding whether one thing caused another before drawing conclusions. Correlation is not enough. Two distinct contexts required before anything is declared a cause.

---

**L14 — Outcome Layer** `user outcome as primary target · correction-resistance`

The teacher who measures success not by how often students ask for help, but by how capable they become independently. If MNEMOS is making the user more reliant on it over time, that is a failure, not a success.

**L15 — Adversarial Layer** `permanent · isolated · FM Register`

The internal critic who never stops. Structurally isolated so it cannot be silenced by other layers. Its only job is to find what is wrong. Runs in every session. Always.

**L16 — Context Policy** `max 5 namespaces · inheritance · drift detection`

The HR policy layer. Different life contexts (work, health, personal) have different rules, different belief priorities, and different thresholds for intervention. Maximum five namespaces to prevent policy explosion.

---

## The Six Belief Domains

| Domain | Trust Level | Truth-Immune | Notes |
|--------|-------------|:------------:|-------|
| `FACTUAL` | Low → oracle validates | ✓ | External claims. Grounding oracle required before promotion |
| `CONSTRAINT` | High + Anchored | ✓ | Allergies, legal, safety. Always surfaces. Typed expiry |
| `PREFERENCE` | High — user is ground truth | | User is the only authority. Never overridden by outcome score |
| `EVALUATIVE` | Medium — attributed | | Assessments, not facts. Source attribution mandatory |
| `IDENTITY` | User-defined | | Multi-stable. Never force-merged across namespaces |
| `CAUSAL` | Medium | | Observed weight vs validated weight. 2+ contexts to validate |

---

## The Failure Mode Register

108 failure modes identified and addressed. A selection across the arc:

| FM | Name | What it was | How it was fixed |
|----|------|-------------|-----------------|
| 01 | Salience ≠ Truth | Importance scores contaminated truth judgments | 5 orthogonal scores, structurally decoupled |
| 47 | Epistemic Sycophancy | System agreed with users to make them feel good | Truth-Preservation Override — 4 immune classes always surface |
| 63 | Identity Coherence Overreach | System tried to merge contradictory identity beliefs | Multi-stable identity — coherence_conflict() never force-merges |
| 87 | Learned Helplessness Loop | 7 direct answers in a row with no reflection | Forced re-entry — topic-aware, only if prior history exists |
| 93 | Preference-Blind Re-entry | FM-87 fired even when user clearly preferred direct answers | Per-topic mode preference tracked; suppresses re-entry at ≥0.65 confidence |
| 98 | Frustration Recovery Failure | "Your answers aren't helping" → system asked for clarification | FrustrationTracker — change approach immediately, no questions |
| 100 | Bullet List as Default Register | Casual conversation got formatted reports | ConversationalRegister — prose instruction for casual turns |
| 101 | Emotion Over-escalation | "Very sad" triggered crisis resources | EmotionIntensityClassifier — LOW / MEDIUM / HIGH tiers |
| 104 | No Social State Tracking | System explained its epistemology under social pressure instead of reading the room | SocialStateTracker — live adversarial/depth/circling model |
| 107 | No Session Memory Compression | Each turn responded in isolation | SessionSynthesizer — compressed user model, updated every 5 turns |

Full register: [`docs/failure_modes.md`](docs/failure_modes.md)

**FM-109+ is open.** The register closes only when the project ends.

---

## What Real Sessions Revealed

Five real human sessions — including one with a complete stranger (Qarmik's wife) who had no briefing — uncovered failure modes that 10,000 simulated turns never surfaced.

The honest finding from `docs/where_mnemos_misreads_humans.md`:

> *MNEMOS does not fail in intelligence. It fails in timing, tone, and restraint.*

Simulation finds annoying failures. Real sessions find a different class — failures that require genuine ambiguity, emotional subtext, and multi-intent phrasing to trigger. That document records exactly what broke and why.

---

## How MNEMOS Differs from MemPalace

MemPalace asks: *what did the user say that is relevant to this query?*

MNEMOS asks: *what do I actually know about this user, how confident am I, should I trust it, and is surfacing it right now good for them?*

MemPalace is a retrieval system. MNEMOS is an attempt at a reasoning system about what it knows about you. The difference matters most at the edges — when two beliefs contradict, when a constraint must surface regardless of relevance score, when the system needs to decide whether helping is actually helping.

---

## Quick Start

```bash
# Optional but recommended
pip install chromadb sentence-transformers rank-bm25

# For real sessions with a live LLM
pip install openai
```

```python
from mnemos_lite import MnemosLite, Domain

m = MnemosLite()
m.new_session()

# Truth-immune constraint — always surfaces
m.add_belief(
    content="User has a severe shellfish allergy",
    domain=Domain.CONSTRAINT,
    ns="health"
)

# Preference — user is ground truth
m.add_belief(
    trait="response_style",
    value="concise",
    context="work/technical",
    ns="work"
)

# Causal observation
m.add_causal("low sleep", "focus drops", context="personal")

context, validation = m.ask("Should I take on this project?", namespace="work")
print(m.digest())  # epistemic footer always included
```

**For real sessions:**

```bash
export OPENAI_API_KEY="your_key_here"
python mnemos_session.py
```

---

## Repo Structure

```
mnemos/
├── mnemos_lite.py                         Core prototype — v0.9, ~1900 lines
├── mnemos_session.py                      Real session runner (OpenAI API)
├── MNEMOS_Architecture_Reference.pdf      Complete continuity document
├── docs/
│   ├── architecture.md                    Full 14-layer specification
│   ├── failure_modes.md                   All 108 failure modes
│   ├── simulation.md                      v0.4 through v0.9 results
│   └── where_mnemos_misreads_humans.md    Observations from 5 real sessions
└── LICENSE
```

---

## Status

Architecture stable. Five real sessions complete. The remaining work is depth, synthesis, and cross-session memory — the gap between a system that responds well and one that genuinely knows you over time.

**FM-109 is waiting in the next session.**

---

## Credits and Acknowledgements

| Role | Who |
|------|-----|
| **Originating Insight** | **Qarmik** — the Memory Pyramid idea that changed the problem from storage to living structure |
| **Implementation and Co-design** | **Claude** (Anthropic) |
| **Adversarial Critic and Co-design** | **ChatGPT / Commander V** (OpenAI) |
| **Catalyst** | **Milla Jovovich** — MemPalace showed what was possible and what remained unsolved |
| **The spark** | **Mei Ling Leung**, AI Engineer at [Embedded LLM](https://embeddedllm.com/about-us/) — her LinkedIn post about MemPalace is what started this |

MNEMOS began because Mei Ling wrote about MemPalace, Qarmik read it, and asked what it didn't solve.

Two AI systems from competing companies, coordinated by a human who changed the question, built architecture that neither would have reached alone. The adversarial process was the method. The human insight was the origin. A LinkedIn post by an engineer who noticed something important was the spark.

---

## License

MIT. See [LICENSE](LICENSE).

---

<div align="center">

*"You cannot have the Muses — poetry, history, music, astronomy — without memory as their mother."*

*That is what MNEMOS is trying to be.*

</div>
