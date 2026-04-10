# MNEMOS

**An AI memory architecture built to serve humans without replacing them.**

Co-evolved through adversarial critique between [Claude](https://anthropic.com) (Anthropic) and [ChatGPT](https://openai.com) (OpenAI), driven by **Qarmik** — April 2026.

---

## What this is

Most AI systems forget you the moment the conversation ends. MNEMOS is a design for AI memory that doesn't just store what you said — it tracks *what you believe*, *what constrains you*, *how you think*, and *how that changes over time*. Then it uses all of it to serve you better, without becoming a crutch.

The core principle, invariant across every version:

> *Store everything. Reason carefully. Trust nothing blindly.*
> *Respond fast. Degrade gracefully. Serve without replacing the human.*

This repository contains the complete architecture specification, a working Python prototype (`mnemos_lite.py`), and the full record of 93 failure modes identified and addressed through adversarial co-design.

---

## How it was built

MNEMOS did not emerge from a single design session. It was stress-tested into existence.

The process: ChatGPT (acting as adversarial critic) identified failure modes. Claude analyzed them, pushed back on the invalid ones, implemented the valid fixes, and ran simulations. Qarmik drove the session, relayed critiques, and made the calls. Seven specification versions. Four rounds of code critique. 93 failure modes addressed. Zero wrong answers in simulation — only annoying ones, which is the right kind of problem to have.

The simulation result that matters most:

| Version | Annoying failures | Wrong failures | Fix |
|---------|:-----------------:|:--------------:|-----|
| v0.4 | 10 | 0 | Baseline |
| v0.5 | 6 | 0 | InteractionMemory |
| v0.6 | 3 | 0 | FM-87–92: re-entry, clustering, resistance |
| v0.7 | 0 | 0 | FM-93: preference-blind re-entry |

The system has been *correct* from the start. The work was making it *not annoying* — which turns out to be harder.

---

## Architecture at a glance

MNEMOS has 14 layers, 9 design axioms, and 6 belief domains.

### The Nine Axioms (nothing in the system may violate these)

| # | Axiom | Meaning |
|---|-------|---------|
| I | Salience ≠ Truth | Importance governs retrieval only — never epistemic status |
| II | Provenance is Permanent | Every belief traces to source; raw records never destroyed |
| III | Uncertainty is First-Class | Every belief carries Beta(α,β); variance matters as much as mean |
| IV | Trust is Tiered | Preferences: high. Self-reported facts: medium. External: low |
| V | Failures Must Be Loud | Silent failures architecturally prohibited |
| VI | Correctness + Speed Coexist | Dual-path: Fast (<50ms) + Deep (async) |
| VII | The System Must Be Legible | Memory Digest: calibrated language, evidence counts, epistemic footer always |
| VIII | Bounded Intelligence Wins | Non-Adaptive Core + convergence criterion |
| IX | Remain Permanently Breakable | L15 Adversarial Layer always active; FM Register always open |

### The Six Belief Domains

| Domain | Trust | Truth-Immune | Notes |
|--------|-------|:------------:|-------|
| `FACTUAL` | Low prior → oracle validates | ✓ | External facts. Grounding oracle required |
| `CONSTRAINT` | High + Anchored | ✓ | Allergies, legal, safety. Typed expiry |
| `PREFERENCE` | High — user is ground truth | | User is authority. Never overridden |
| `EVALUATIVE` | Medium — attributed | | Assessments, not facts. Mandatory attribution |
| `IDENTITY` | User-defined | | Multi-stable. Never force-merged |
| `CAUSAL` | Medium | | Observed vs validated weight |

### The 14 Layers

```
L0   Fast Path          <50ms real-time, TTL 72h
L1   Episodic Store     Verbatim write-once, BM25+dense hybrid search
L2   Knowledge Graph    Beta(α,β) nodes, bounded influence propagation
L3   Semantic Store     Async consolidation, versioned snapshots
L4   Inference Engine   Read-only context assembly, intent-aware
L5   Safety Layer       Anomaly detection, circuit breakers
L6   Audit Log          Immutable append-only, signed records
L7   Grounding Oracle   External validation for FACTUAL domain only
L8   Token Budget       Progressive loading: Core 120T → Essential 500T
L9   Memory Digest      Calibrated render, evidence counts, epistemic footer
L10  Meta-Memory        Self-evaluation, bounded by RWB cap + epsilon-floor
L11  Arbitration        Cross-path conflict resolution with SLAs
L12  Non-Adaptive Core  IDENTITY: frozen. CONSTRAINT: typed expiry
L13  Causal Attribution Gates all L10 updates with causal analysis
L14  Outcome Layer      User outcome as primary optimization target
L15  Adversarial Layer  Permanent internal critic, FM Register, isolated
L16  Context Policy     Namespace-scoped (max 5), drift detection
```

---

## Quick start

```bash
# Optional — enables vector search and BM25
pip install chromadb sentence-transformers rank-bm25

# Works with stdlib only if you skip the above
```

```python
from mnemos_lite import MnemosLite, Domain

m = MnemosLite()
m.new_session()

# Add a safety constraint — always surfaces, truth-immune
m.add_belief(
    content="User has a severe shellfish allergy",
    domain=Domain.CONSTRAINT,
    ns="health"
)

# Add a preference — user is ground truth
m.add_belief(
    trait="response_style",
    value="concise",
    context="work/technical",
    ns="work"
)

# Add a causal observation
m.add_causal("low sleep", "focus drops", context="personal")

# Ask a question — returns context packet + interaction decision
context, validation = m.ask("Should I take on this project?", namespace="work")

print(f"Reflect: {validation['reflect']} ({validation['reflect_reason']})")
print(m.digest())  # epistemic footer always included
```

---

## The failure mode register

93 failure modes identified and addressed. A selection:

- **FM-01** Salience ≠ Truth — importance scoring decoupled from epistemic status at the architecture level
- **FM-47** Epistemic Sycophancy — Truth-Preservation Override; 4 immune classes that surface regardless of user preference
- **FM-63** Identity Coherence Overreach — multi-stable identity; `coherence_conflict()` never force-merges across namespaces
- **FM-87** Learned Helplessness Loop — forced reflection re-entry after 7 direct answers, topic-aware
- **FM-90** False Positive Resistance — confidence-gated: 1 signal = 0.25, 2 signals = 0.65, 3+ = 0.90; only suppress at ≥0.65
- **FM-93** Preference-Blind Re-entry — per-topic mode preference tracked in `LongTermBehavior`; suppresses FM-87 re-entry at confidence ≥0.65

Full register: [`docs/failure_modes.md`](docs/failure_modes.md)

**FM-94+ is open.** The register closes only when the project ends.

---

## Repo structure

```
mnemos/
├── mnemos_lite.py                     # Working prototype — v0.7, 1399 lines
├── docs/
│   ├── architecture.md                # Full 14-layer spec
│   ├── failure_modes.md               # All 93 FMs
│   └── simulation.md                  # v0.4→v0.7 results
└── MNEMOS_Architecture_Reference.pdf  # Complete continuity document
```

---

## Status

**Behavioral tuning phase.** Architecture is stable. No new layers needed. The next meaningful signal comes from real human sessions, not theory.

FM-94+ is waiting in the first real session.

---

## Credits

| Role | Who |
|------|-----|
| Human Architect | **Qarmik** |
| Implementation & Co-design | **Claude** (Anthropic) |
| Adversarial Critic & Co-design | **ChatGPT / Commander V** (OpenAI) |

This project demonstrates something worth naming: two AI systems from competing companies, coordinated by a human, produced better architecture than either would have alone. The adversarial process wasn't a liability. It was the method.

---

## License

MIT. See [`LICENSE`](LICENSE).
