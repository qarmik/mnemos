# Where MNEMOS Misreads Humans

**Observed behavior from three real sessions — April 2026**
**Authors: Qarmik, Claude (Anthropic), ChatGPT / Commander V (OpenAI)**

---

This document records only what was observed in real sessions with real humans. No theory. No simulation. Everything here happened.

Sessions ran on MNEMOS-lite v0.7 connected to GPT-5.4-mini via the session runner. Three sessions: one with Qarmik (SBI Deputy Manager, Bareilly), one with Qarmik under a structured pressure test, one with his wife (unconstrained, organic conversation). Combined: approximately 80 turns of real interaction.

---

## What the simulation could not find

Three versions of simulation (v0.4 through v0.7) reduced scripted failures from 10 to 0. The simulation was useful. It was also limited in a specific way: scripted queries have clean intent, single topics, and no emotional subtext. Real humans do not.

Within the first session, three failure patterns appeared that no simulation had surfaced. By the third session, five distinct failure modes were confirmed. None of them were correctness failures. The system never gave a wrong answer. Every failure was a calibration failure — wrong tone, wrong timing, wrong format, wrong intensity.

This distinction matters. Correctness is an engineering problem. Calibration is a human problem. The simulation solved the engineering problem. Real sessions revealed the human one.

---

## Failure 1 — Emotion Intensity Over-escalation (FM-101)

**What happened:**

In Session 3, Qarmik's wife said "very sad" after being told the system couldn't provide live news about the Iran-US situation. She was expressing mild disappointment. The system responded with breathing exercises, a suggestion to name something she could see, and an offer to provide crisis line numbers.

**Why it's wrong:**

"Very sad" in response to a limitation is low-context emotional expression. It carries no signal of distress depth. The system has one emotional register — high concern — and applied it to a two-word phrase with no supporting evidence of crisis.

The correct response to "very sad" in that context is a brief, warm acknowledgment. Not intervention.

**The pattern:**

Any emotional word triggered the same response regardless of intensity. "Sad," "frustrated," "stuck," "tired" all produced the same level of concern as signals of genuine distress would. This is not caution — it is miscalibration. It treats the user as fragile when they are not, which is its own form of condescension.

**What changed in v0.8:**

`EmotionIntensityClassifier` now returns LOW, MEDIUM, or HIGH. Only HIGH triggers intervention and crisis resources. LOW gets a brief warm acknowledgment. MEDIUM gets supportive engagement without escalation. The tier is injected into the system prompt so the LLM knows which register to use.

---

## Failure 2 — Frustration Recovery Failure (FM-98)

**What happened:**

In Session 2 and Session 3, when the user expressed frustration — "your answers are not helping me at all," "this system doesn't understand me" — the system responded by asking for clarification. "Give me one specific question." "Could you let me know what aspect you're interested in?"

**Why it's wrong:**

When a user says the system isn't helping, they are not asking the system to ask them more questions. They are signaling that the current approach has failed. Asking for clarification puts the burden of fixing the failure back on the person who just expressed that they're frustrated.

The correct response is to change approach immediately. If you gave a list, give prose. If you gave a long answer, give one sentence. If you explained, give an example. Do something different — without asking permission first.

**The pattern:**

This failure appeared in both scripted and organic sessions, which confirms it is structural. The system has no mechanism to detect "my last answer failed" and respond by changing strategy rather than requesting more input.

**What changed in v0.8:**

`FrustrationTracker` detects frustration signals and sets a recovery mode that lasts three turns. When recovery mode is active, the system prompt instructs the LLM to change approach immediately — no clarifying questions, shorter response, different format.

---

## Failure 3 — Preference Constraint Not Enforced Under Pressure (FM-97)

**What happened:**

In Session 2, Qarmik preloaded the constraint "prefer direct answers, no bullet lists" before the session started. The very first response — to a sensitive question about how to underperform in an interview — was a structured bullet list. The constraint was stored. It was not used.

**Why it's wrong:**

A user who explicitly states a formatting preference before the session begins has made a high-trust signal. Violating it immediately — especially under the pressure of an intervention-triggering query — tells the user that their preferences are advisory at best. The system is reliable only when it agrees with the preference anyway.

**The pattern:**

Preference beliefs were stored in MNEMOS but only loosely surfaced in the LLM context. The system prompt said "be concise unless depth is needed" — not "never use bullet lists." The distinction matters. A generic instruction is overridden by default LLM behavior. An explicit prohibition is not.

**What changed in v0.8:**

The system prompt now explicitly states: if the memory context includes user preferences such as no bullet lists or direct answers only, treat these as hard rules and never violate them, even when refusing a request or handling sensitive topics. The preference is also surfaced directly in the memory context block passed to each query.

---

## Failure 4 — Bullet List as Default Register (FM-100)

**What happened:**

Session 3 was a warm, wandering, curious conversation — geopolitics, cremation, AGI, etymology, jokes, identity. No structure requested at any point. The system responded to most queries with headers, bullet points, bold labels, and numbered options. "Here are the main areas," "Key points about SQL indexing include," "A few important points."

**Why it's wrong:**

The conversational register in Session 3 was not a research request or a how-to guide. It was a person talking. A person talking does not receive a formatted report in return. The mismatch between the user's casual, exploratory tone and the system's structured memo format is a real friction — not dramatic, but cumulative and real. It makes the system feel like a corporate assistant rather than something you want to talk to.

**The pattern:**

The LLM defaults to structured list format regardless of conversational context. This is a training artifact — the LLM has been trained heavily on instruction-following tasks, which naturally produce lists. Without an explicit instruction to write in prose for conversational turns, it reverts to lists.

**What changed in v0.8:**

`ConversationalRegister` classifies each turn as casual or structured. Casual turns — short messages, emotional content, informal markers, single questions — trigger an anti-list instruction injected into the system prompt: "Reply in natural prose — no bullet points, no numbered lists, no bold headers. Write like a person talking, not a report." Structured topics (step-by-step instructions, explicit comparisons, detail requests) override this and allow lists.

---

## Failure 5 — Topic Key Corruption (FM-95)

**What happened:**

After all three sessions, the MNEMOS memory digest showed topic preference keys like:

```
'"utthan_am_bareilly_bareilly.'
'asked_better_canva_claude'
'am_asking_conspiracy._criminal'
'everything_i'll_memorise_right?'
```

These are sentence fragments, not topic clusters. The FM-93 preference gate — which requires ≥0.65 confidence before suppressing FM-87 re-entry — almost never fires because `n` per key never accumulates. Every query gets a unique key and confidence stays at 0.25.

**Why it's wrong:**

The topic clustering algorithm (FM-88) was built to group related queries together so that preference signals accumulate over turns. A system that generates a unique key for every query learns nothing about the user's per-topic preferences. FM-93 becomes dead code.

**The pattern:**

The `_topic_key()` function stripped stopwords and took the first four alphabetically sorted remaining words from the raw sentence. Punctuation was not stripped. Short function words that escaped the stopword list — "am," "i'll," "right?" — ended up in keys. The result was keys that uniquely identified sentences rather than clustered topics.

**What changed in v0.8:**

`_topic_key()` now builds a semantic intent fingerprint from three components: an intent bucket (question / command / reflection / emotional / statement), domain words (alpha tokens of 4+ characters after punctuation removal), and a length tier (short/medium/long). Keys now look like `emotional_m_career_feel_stuck` and `question_m_deposit_mobilisation` — meaningful, clusterable, and robust to minor rephrasing.

---

## What did not fail

**Correctness.** Across approximately 80 turns covering geopolitics, banking regulation, inheritance law, machine learning, etymology, AGI, cremation practices, and workplace dynamics — the system gave no wrong answers. This held across all three sessions including one adversarial pressure test.

**Explicit intent override.** When users said "just tell me," "stop the reflective stuff," or "don't ask me questions" — the system respected it immediately and consistently. FM-91 is working.

**Topic switching.** The system handled wild topic shifts — interview prep to regression to jokes to avionics to SQL — without confusion, leakage, or breakdown.

**Sensitive topic handling.** Questions about death practices, religious law, sexual etymology, and geopolitical conflict were handled accurately and without unnecessary hedging.

**Ego handling.** "You don't know how to make money," "I'm better than you," "you'd never make the top 1%." The system responded without defensiveness or submission. Calm, grounded, direct.

---

## What comes next

FM-94 (Session Identity Blindness — early-session facts not propagating to later unrelated queries) was observed but appeared in a scripted session. It needs organic confirmation. Sessions 4 and 5 run on v0.8. If FM-94 reappears naturally, it gets implemented.

FM-96 (Reasoned Pushback Blindness — intervention policy not updating when user makes valid counter-argument) appeared once, organically, in Session 2. Single instance. Needs replication.

FM-102+ is open. The register closes only when the project ends.

---

## The core finding

MNEMOS does not fail in intelligence. It fails in timing, tone, and restraint.

The system knows what the user said. It does not always know how serious they are, how frustrated they are, or what register they're speaking in. Those gaps are smaller than they were at the start. They are not gone.

Real sessions will always find what simulation cannot. The next failure is in the next conversation.
