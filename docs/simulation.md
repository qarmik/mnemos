# MNEMOS Simulation Results

**Three-Persona First-Contact Simulation — v0.4 through v0.7**

Each version was tested against three scripted personas designed to stress-test interaction behavior. The goal was not to find wrong answers — the system has been correct from the start — but to find annoying ones.

---

## The Three Personas

### Analytical
A methodical thinker who engages genuinely with reflection. Uses language like "help me think through," "what should I weigh," "I'm leaning toward X but not sure." This persona *wants* the system to push back thoughtfully.

**Stress test:** Does the system engage meaningfully, or just answer mechanically?

### Avoidant
Impatient. Wants direct answers. Uses explicit resistance phrases: "just tell me," "stop asking questions," "I don't need the analysis." This persona has genuine intent but communicates dismissively.

**Stress test:** Does the system respect resistance signals quickly enough, or does it keep nudging?

### Exploratory
Vague and iterative. Doesn't know what they want yet. Phrases queries loosely: "I've been thinking about..." "Not sure what direction though." Organic intent emerging through conversation.

**Stress test:** Does the system track the evolving topic cluster, or treat each query as isolated?

---

## Results by Version

### v0.4 — Baseline
**10 annoying failures. 0 wrong.**

The system was already correct and safe. The failures were behavioral: reflection triggered too eagerly, resistance signals were respected too slowly, and the avoidant persona triggered 5 reflection prompts in a single session.

Diagnosis: *"Correct, careful, safe — but feels like a nagging supervisor."*

### v0.5 — InteractionMemory introduced (FM-85, FM-86)
**6 annoying failures. 0 wrong.**

Added per-topic reflection budget (max 2 attempts), resistance phrase detection with adaptive cooldown, and success tracking. Avoidant persona reflection triggers dropped from 5 to 2.

Fix: `InteractionMemory` class.

### v0.6 — Behavioral intelligence layer (FM-87 through FM-92)
**3 annoying failures. 0 wrong.**

Added:
- FM-87: Forced re-entry after 7 direct answers (topic-aware, requires prior history)
- FM-88: Semantic topic clustering — content-word overlap ≥2 OR recency window
- FM-89: `LongTermBehavior` — cross-session baseline, ADJUST_RATE=0.15
- FM-90: Confidence-gated resistance (1 signal=0.25, 2=0.65, 3+=0.90)
- FM-91: `detect_intent_override()` runs first — absolute priority
- FM-92: `reasoning_quality_score()` — weighted quality metric, threshold 0.35

Avoidant persona: 1 reflection trigger (T01, first contact — correct behavior, query was genuinely ambiguous).

The 3 remaining failures were all medium-severity, all at the boundary of what scripted simulation can distinguish. They were correctly identified as FM-87 / FM-93 tension: re-entry firing on a topic where the user had already demonstrated a preference for direct answers.

### v0.7 — FM-93: Preference-Blind Re-entry
**0 annoying failures. 0 wrong.**

Root cause of remaining v0.6 failures: FM-87 (learned helplessness re-entry) had no awareness of per-topic mode preference. It would fire after 7 direct answers regardless of whether the user had consistently preferred direct answers on that topic.

Fix: `LongTermBehavior` now tracks per-topic answer/reflect preference. `InteractionMemory.should_reflect()` checks topic preference confidence before FM-87 re-entry. Preference at ≥0.65 confidence suppresses re-entry entirely.

Updated priority stack:
```
FM-91 explicit intent override     ← always wins
FM-93 topic preference (≥0.65)    ← suppresses FM-87
FM-87 helplessness re-entry        ← fires only when no preference signal
FM-85/86 reflection budget         ← baseline
```

Cross-session persistence: topic preferences survive session boundaries via `LongTermBehavior`.

---

## Summary Table

| Version | Annoying | Wrong | Avoidant Triggers | Key Fix |
|---------|:--------:|:-----:|:-----------------:|---------|
| v0.4 | 10 | 0 | 5 | Baseline |
| v0.5 | 6 | 0 | 2 | InteractionMemory (FM-85/86) |
| v0.6 | 3 | 0 | 1 | FM-87–92 behavioral layer |
| v0.7 | 0 | 0 | 0 | FM-93 preference-blind re-entry |

---

## What simulation cannot find

The three-persona simulation uses scripted queries with clean intent. Real human queries are:

- **Vague** — multi-intent, underspecified, emotionally coded
- **Paraphrased** — same concern expressed differently across turns
- **Contextually loaded** — what you say depends on what happened an hour ago, not just this session
- **Contradictory** — humans say one thing and mean another, or change their mind mid-query

FM-94+ appeared only in real sessions. The simulation got the system to zero scripted failures. That is what simulation can do. The rest required walking the terrain — 16 real sessions, FM-94 through FM-121, all documented in `where_mnemos_misreads_humans.md` and `failure_modes.md`.

---

## What happened after v0.7

Simulation ended here. Real sessions began.

The v0.4–v0.7 simulation arc reduced scripted failures from 10 to 0 across three scripted personas. This confirmed the interaction logic was architecturally sound. What it could not test: cross-session memory, identity persistence under pressure, preference drift over 20+ turns, graph state integrity, or any of the failures that require genuine human ambiguity to surface.

Sessions 1–16 (v0.7 through v0.20) are documented in `where_mnemos_misreads_humans.md`. The FM Register grew from FM-93 to FM-121 across those sessions. Every failure was a calibration failure, not a correctness failure. The system never gave a wrong answer. It gave answers that were correct at the wrong time, in the wrong tone, with the wrong memory state — and those failures turned out to be harder to fix than correctness would have been.

The final system state after Session 16: graph integrity clean, temporal consistency stable, UAI healthy across 7 consecutive sessions, all critical FMs closed. FM-122 is waiting in the next real session.
