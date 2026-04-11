# MNEMOS

**An AI memory architecture built to serve humans without replacing them.**

---

## How it started

In early 2026, **Qarmik** came across a LinkedIn post by Mei Ling Leung — an AI engineer at Embedded LLM — writing about MemPalace, an open-source AI memory system built by actress and technologist Milla Jovovich using Claude.

The post made a simple observation that stopped him: Alice in Resident Evil wakes up with no memory across six films, fighting to reconstruct who she is from fragments. That is not fiction. That is the AI memory problem. Every session ends, context vanishes, the model starts over. Umbrella is the session boundary.

Jovovich's answer with MemPalace was elegant: don't extract facts from conversations. Store everything verbatim. Organize it hierarchically. Let structure do the filtering before the vector search fires.

Qarmik read the repo, understood what it solved, and then asked the harder question: what does it not solve?

That question became MNEMOS.

The insight Qarmik brought was this: what if memory wasn't storage at all, but a living structure — where beliefs compete, rise, fall, and reshape each other over time? Not a warehouse with a search engine. A political system where ideas compete, power shifts, and conflicts get resolved.

That reframing changed everything. Every layer in MNEMOS is a consequence of taking it seriously. The arbitration engine, the trust tiers, the decay functions, the autonomy preservation, the adversarial layer — none of those are features bolted onto a storage system. They are what happens when you follow the Memory Pyramid idea to its conclusions.

ChatGPT named it precisely: before Qarmik, MNEMOS would have been a better database. Because of Qarmik, it became a thinking system attempt.

---

## What MNEMOS is

MNEMOS is a human-centered AI memory architecture. It stores conversation history, user beliefs, preferences, constraints, identity states, and causal patterns — and uses them to make an AI assistant genuinely personalized over time.

The core principle, invariant across every version:

> *Store everything. Reason carefully. Trust nothing blindly.*
> *Respond fast. Degrade gracefully. Serve without replacing the human.*

This repository contains the complete architecture specification, a working Python prototype, five sessions of real human interaction data, and the full record of 108 failure modes identified and addressed through adversarial co-design.

---

## How MNEMOS differs from MemPalace

MemPalace asks: *what did the user say that is relevant to this query?*

MNEMOS asks: *what do I actually know about this user, how confident am I, should I trust it, and is surfacing it right now good for them?*

That is a different class of question.

MemPalace stores what was said. MNEMOS stores what is believed, with uncertainty attached. A shellfish allergy surfaces in every relevant context regardless of retrieval score — not because the query mentioned food, but because some facts are truth-immune and must always surface. MemPalace has no equivalent. Salience and truth are the same thing in MemPalace. Axiom I of MNEMOS says they must be structurally separated.

MNEMOS also tracks whether the user is becoming dependent on the system over time, maintains a permanent internal critic that challenges its own stable beliefs, and governs the entire conversational interaction — not just what to retrieve, but when to reflect, when to intervene, when to stay quiet, and when the system is doing harm by being too helpful.

MemPalace is a well-built retrieval system. MNEMOS is an attempt at a reasoning system about what it knows about you.

---

## How it was built

MNEMOS was stress-tested into existence through adversarial co-evolution.

The process: ChatGPT (acting as adversarial critic, codenamed Commander V) identified failure modes. Claude analyzed them, pushed back on the invalid ones, implemented the valid fixes, and ran simulations. Qarmik drove the session, relayed critiques, made the calls, and ran real human sessions to find what simulation could not.

Seven specification versions. Four rounds of code critique. Five real human sessions. 108 failure modes addressed.

| Version | Annoying failures | Wrong failures | Fix |
|---------|:-----------------:|:--------------:|-----|
| v0.4 | 10 | 0 | Baseline |
| v0.5 | 6 | 0 | InteractionMemory |
| v0.6 | 3 | 0 | FM-87 through FM-92 |
| v0.7 | 0 | 0 | FM-93: preference-blind re-entry |
| v0.8 | 0 | 0 | FM-95 through FM-101: real-session calibration |
| v0.9 | 0 | 0 | FM-102 through FM-108: social intelligence layer |

The system has been correct from the start. The work was making it not annoying — and then not tone-deaf — which turned out to be harder than correctness.

---

## Architecture at a glance

14 layers, 9 design axioms, 6 belief domains.

### The Nine Axioms

| # | Axiom | Meaning |
|---|-------|---------|
| I | Salience != Truth | Importance governs retrieval only, never epistemic status |
| II | Provenance is Permanent | Every belief traces to source; raw records never destroyed |
| III | Uncertainty is First-Class | Every belief carries Beta(alpha,beta); variance matters as much as mean |
| IV | Trust is Tiered | Preferences: high. Self-reported facts: medium. External: low |
| V | Failures Must Be Loud | Silent failures architecturally prohibited |
| VI | Correctness + Speed Coexist | Dual-path: Fast (<50ms) + Deep (async) |
| VII | The System Must Be Legible | Memory Digest with calibrated language and epistemic footer always |
| VIII | Bounded Intelligence Wins | Non-Adaptive Core + convergence criterion |
| IX | Remain Permanently Breakable | L15 Adversarial Layer always active; FM Register always open |

### The 14 Layers

```
L0   Fast Path          <50ms real-time, TTL 72h
L1   Episodic Store     Verbatim write-once, BM25+dense hybrid search
L2   Knowledge Graph    Beta(alpha,beta) nodes, bounded influence propagation
L3   Semantic Store     Async consolidation, versioned snapshots
L4   Inference Engine   Read-only context assembly, intent-aware
L5   Safety Layer       Anomaly detection, circuit breakers
L6   Audit Log          Immutable append-only, signed records
L7   Grounding Oracle   External validation for FACTUAL domain only
L8   Token Budget       Progressive loading: Core 120T to Essential 500T
L9   Memory Digest      Calibrated render, evidence counts, epistemic footer
L10  Meta-Memory        Self-evaluation, bounded by RWB cap and epsilon-floor
L11  Arbitration        Cross-path conflict resolution with SLAs
L12  Non-Adaptive Core  IDENTITY: frozen. CONSTRAINT: typed expiry
L13  Causal Attribution Gates all L10 updates with causal analysis
L14  Outcome Layer      User outcome as primary optimization target
L15  Adversarial Layer  Permanent internal critic, FM Register, isolated
L16  Context Policy     Namespace-scoped (max 5), drift detection
```

---

## What real sessions revealed

Five real human sessions uncovered failure modes that simulation never surfaced:

**FM-101** — System escalated to crisis resources when user said "very sad" after a news limitation. Fixed: three-tier emotion classifier (LOW / MEDIUM / HIGH).

**FM-100** — System responded to casual conversation with formatted bullet reports. Fixed: conversational register detection injects anti-list instruction.

**FM-98** — When user said "your answers aren't helping," system asked for clarification instead of changing approach. Fixed: frustration recovery mode.

**FM-104** — System kept explaining its epistemology across four rounds of social pressure instead of reading the room. Fixed: social state tracker with adversarial signal detection.

**FM-106** — System described surface symptoms without naming the mechanism underneath. Fixed: depth invitation detection injects "go one inference deeper" instruction.

**FM-107** — Each turn responded in isolation; no compressed model of who the user is across the session. Fixed: session synthesizer builds and persists user model.

The honest finding: MNEMOS does not fail in intelligence. It fails in timing, tone, and restraint.

---

## Quick start

```bash
pip install openai
pip install chromadb sentence-transformers rank-bm25   # optional
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

context, validation = m.ask("Should I take on this project?", namespace="work")
print(m.digest())
```

For real sessions with a live LLM:

```bash
export OPENAI_API_KEY="your_key"
python mnemos_session.py
```

---

## Repo structure

```
mnemos/
├── mnemos_lite.py                        v0.9 prototype, ~1900 lines
├── mnemos_session.py                     Real session runner (OpenAI API)
├── docs/
│   ├── architecture.md                   14 layers, 9 axioms, priority stack
│   ├── failure_modes.md                  All 108 FMs
│   ├── simulation.md                     v0.4 through v0.9 results
│   └── where_mnemos_misreads_humans.md   Observations from real sessions
└── MNEMOS_Architecture_Reference.pdf     Complete continuity document
```

---

## Status

Architecture stable. Five real sessions complete. The remaining work is depth, synthesis, and cross-session memory — the gap between a system that responds well and one that actually knows you over time.

FM-109+ is waiting in the next session.

---

## Credits and acknowledgements

| Role | Who |
|------|-----|
| Originating Insight | **Qarmik** — Memory Pyramid, redefined the problem from storage to living structure |
| Implementation and Co-design | **Claude** (Anthropic) |
| Adversarial Critic and Co-design | **ChatGPT / Commander V** (OpenAI) |
| Catalyst | **Milla Jovovich** — MemPalace showed what was possible and what remained unsolved |
| The post that started it | **Mei Ling Leung**, AI Engineer at Embedded LLM ([embeddedllm.com](https://embeddedllm.com/about-us/)) |

MNEMOS began because Mei Ling wrote about MemPalace, Qarmik read it, and asked what it didn't solve. That is the actual origin of this project.

Two AI systems from competing companies, coordinated by a human who changed the question, produced architecture that neither would have reached alone. The adversarial process was the method. The human insight was the origin. And a LinkedIn post by an engineer who noticed something important was the spark.

---

## License

MIT. See LICENSE.
