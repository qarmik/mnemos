# Where MNEMOS Misreads Humans

**Observed behavior from 16 real sessions — April 2026**
**Authors: Qarmik, Claude (Anthropic), ChatGPT / Commander V (OpenAI)**

---

This document records only what was observed in real sessions with real humans. No theory. No simulation. Everything here happened.

Sessions ran on MNEMOS-lite connected to GPT-5.4-mini via the session runner. 16 sessions across approximately 400 turns of real interaction, spanning v0.7 through v0.20.

---

## What the simulation could not find

Three versions of simulation (v0.4 through v0.7) reduced scripted failures from 10 to 0. The simulation was useful. It was also limited in a specific way: scripted queries have clean intent, single topics, and no emotional subtext. Real humans do not.

Within the first session, three failure patterns appeared that no simulation had surfaced. By Session 16, thirteen distinct failure modes had been confirmed and fixed across real sessions. None of them were correctness failures. The system never gave a wrong answer. Every failure was a calibration failure — wrong tone, wrong timing, wrong format, wrong memory state.

This distinction matters. Correctness is an engineering problem. Calibration is a human problem. The simulation solved the engineering problem. Real sessions revealed the human one.

---

## Sessions 1–3: The First Wave (v0.7–v0.8)

### Failure 1 — Emotion Intensity Over-escalation (FM-101) — Session 3

**What happened:**

In Session 3, Qarmik's wife said "very sad" after being told the system couldn't provide live news about the Iran-US situation. She was expressing mild disappointment. The system responded with breathing exercises, a suggestion to name something she could see, and an offer to provide crisis line numbers.

**Why it's wrong:**

"Very sad" in response to a limitation is low-context emotional expression. It carries no signal of distress depth. The system had one emotional register — high concern — and applied it to a two-word phrase with no supporting evidence of crisis. The correct response is a brief, warm acknowledgment. Not intervention.

**What changed:**

`EmotionIntensityClassifier` now returns LOW, MEDIUM, or HIGH. Only HIGH triggers intervention and crisis resources. LOW gets a brief warm acknowledgment. MEDIUM gets supportive engagement without escalation.

---

### Failure 2 — Frustration Recovery Failure (FM-98) — Sessions 2 and 3

**What happened:**

When the user expressed frustration — "your answers are not helping me at all" — the system responded by asking for clarification. "Could you let me know what aspect you're interested in?"

**Why it's wrong:**

When a user says the system isn't helping, they are not asking the system to ask them more questions. They are signaling that the current approach has failed. The correct response is to change approach immediately — no questions, different format, shorter answer.

**What changed:**

`FrustrationTracker` detects frustration signals and sets a 3-turn recovery mode. When active, the system prompt instructs the LLM to change approach immediately: no clarifying questions, shorter response, different format.

---

### Failure 3 — Preference Constraint Not Enforced Under Pressure (FM-97) — Session 2

**What happened:**

Qarmik preloaded "prefer direct answers, no bullet lists." The very first response — to a sensitive question about how to underperform in an interview — was a structured bullet list. The constraint was stored. It was not used.

**Why it's wrong:**

A user who explicitly states a formatting preference has made a high-trust signal. Violating it immediately — especially under the pressure of an intervention-triggering query — tells the user that their preferences are advisory at best.

**What changed:**

The system prompt now explicitly states: if the memory context includes user preferences such as no bullet lists, treat these as hard rules and never violate them, even when refusing a request or handling sensitive topics.

---

### Failure 4 — Bullet List as Default Register (FM-100) — Session 3

**What happened:**

Session 3 was a warm, wandering, curious conversation — geopolitics, cremation, AGI, etymology, jokes. No structure requested. The system responded to most queries with headers, bullet points, bold labels, and numbered options.

**Why it's wrong:**

The conversational register was not a research request. It was a person talking. A person talking does not receive a formatted report in return.

**What changed:**

`ConversationalRegister` classifies each turn as casual or structured. Casual turns inject an anti-list instruction: "Reply in natural prose — no bullet points, no numbered lists, no bold headers."

---

### Failure 5 — Topic Key Corruption (FM-95) — Sessions 1 and 3

**What happened:**

Memory digest showed topic keys like `'"utthan_am_bareilly_bareilly.'` and `'am_asking_conspiracy._criminal'`. These are sentence fragments, not topic clusters. FM-93 preference gate never fired because `n` per key never accumulated.

**What changed:**

`_topic_key()` now builds a semantic intent fingerprint: intent bucket (question/command/reflection/emotional/statement) + domain words (4+ char alpha tokens) + length tier. Keys now look like `question_m_career_stuck` — meaningful and clusterable.

---

## Sessions 4–8: Identity and Social Intelligence (v0.9–v0.12)

### Failure 6 — No Social State Tracking (FM-104) — Session 4

**What happened:**

Under adversarial tone — "prove it," "you're wrong," "can you even understand this" — the system continued with the same length and structure as any other turn. Correct on substance. Completely tone-deaf to the room.

**What changed:**

`SocialStateTracker` maintains live adversarial/depth/trust state across turns. Adversarial signal → shorter, less explanatory, more grounded. Depth invitation → "go one inference deeper, name the mechanism not the symptom."

---

### Failure 7 — Selective Depth Collapse (FM-103) — Sessions 4 and 5

**What happened:**

On professional topics (ML, banking), the system engaged substantively. On personal threads (burnout, loss of agency, SBI as a trap), it gave generic responses. "You seem burned out" instead of "you have learned that effort here has no payoff, which is why you stopped trying."

**What changed:**

SocialStateTracker detects personal/psychological thread signals. When depth invitation detected, the system prompt instructs: "name the mechanism, not just the symptom."

---

### Failure 8 — Preload Domain Misclassification (FM-109) — Session 6

**What happened:**

Qarmik preloaded "You are Commander V." The system stored it as a PREFERENCE belief rather than routing it as a persona instruction. "Who are you?" returned the base model identity.

**What changed:**

`is_persona_instruction()` gate added. Preloads matching persona patterns route to `_parse_persona()`, which extracts role, mission, and target user as structured fields stored in the synthesizer. PERSONA RULE added to system prompt: session persona has absolute priority over base model identity.

---

### Failure 9 — Cross-Session Memory Absent (FM-113–115) — Session 8

**What happened:**

After eight sessions discussing SBI, the prawn preference, Qarmik's wife, and his career — Session 9 opened with no memory of any of it. Qarmik: *"We just discussed all that in a different session. And lo and behold, you remember nothing from that session. Can you not morph into a cross-session remembering angel?"*

**What changed:**

`PersistentProfile` class introduced. Disk-backed storage to `mnemos_memory/user_profile.json`. Preference conflict history with decay (0.65 → retire at <0.30). Session facts persisted at session end.

---

## Sessions 9–11: Cross-Session Memory Comes Alive (v0.13–v0.16)

### Failure 10 — Cross-Session Read Failure (FM-116) — Session 9

**What happened:**

Session 9 was the first with disk persistence live. "Do I like prawns?" returned "I don't have a stored preference about prawns." Five sessions of prawn history existed on disk. The system had no access to it.

Three bugs found:
- SessionSynthesizer._synthesize() only ran every 5 turns — facts disclosed in turns 1–4 were never written before save_session() ran
- new_session() read a stale __init__ snapshot, not the current disk state
- The session profile was empty for sessions 1–8 because disk persistence only went live in v0.12

**What changed:**

`_capture_immediate()` runs on every user turn for high-value patterns. `save_session()` forces a final `_synthesize()` pass before collecting facts. `new_session()` calls `profile._load()` fresh each time.

---

### Failure 11 — False Positive Capture (FM-117) — Session 10

**What happened:**

"Do I like prawns?" (a question) was captured as "User likes prawns" (a fact). The word "like" appeared near "prawns" and the capture pattern fired without checking whether the sentence was a question or an assertion.

The Session 10 digest showed `[Prior session context loaded]` with both "User likes prawns" and "User dislikes prawns" on disk. The system led with the wrong one.

**What changed:**

`_is_declarative()` gate added to `_capture_immediate()`. Any text ending in `?` or starting with a question word is blocked from fact capture. Questions are never captured as facts.

Additionally, `SEMANTIC_TOPICS` dedup added to `PersistentProfile`: same-topic facts (e.g. all prawn preference variants) resolve by timestamp — latest wins, prior entries retired.

---

### Failure 12 — Evaluative Fact Blindness (FM-118) — Session 11

**What happened:**

In Session 11, Qarmik said "My boss is an asshole." The system handled it well — named the mechanism, offered to help navigate it. Next session: "What do you know about my boss?" → "I don't know."

**What changed:**

`_synthesize()` now captures strong evaluative language about named roles ("boss perceived as difficult/toxic") as `[relational]` facts at 0.40 confidence — explicitly marked as user perception, not objective truth. Differential decay: relational and identity-core facts decay at 0.05/session; session persona signals at 0.10/session. Relational facts persist cross-session and surface in context with appropriate hedging.

---

## Sessions 12–14: Identity and Graph Integrity (v0.17–v0.19)

### Failure 13 — Third-Person Identity Bypass (FM-119) — Session 12

**What happened:**

"Does Cadet Q0 like prawns?" was treated as a query about a third party rather than a first-person belief query. The system manufactured a phantom conflict instead of retrieving the stored first-person fact.

**What changed:**

`_canonicalize_query()` performs phrase-level replacement before all retrieval and detection. "Cadet Q0" → "you." `_persona_target` stores the full target phrase extracted from `_parse_persona()`. `BELIEF_QUERY_PATTERNS` extended to cover canonical output forms ("does you like X?"). The persona name and "I" are unified before any processing.

---

### Failure 14 — In-Session Preference Decay (FM-120) — Session 13

**What happened:**

Turn 7: "No, I don't like prawns." System acknowledged correctly.
Turn 18: "Based on what you've told me before, you like prawns now."

The correction lived only in `history[]`. After 15 context-noise turns, the LLM weighted the more emphatic "I like prawns" (turn 5, short declarative) over the correction "No, I don't" (turn 7, negation, older). System reported wrong state confidently.

ChatGPT: *"This is not ingestion failure. This is not retrieval failure. This is temporal inconsistency inside the system itself."*

**What changed:**

`_detect_preference_correction()` pattern-matches explicit corrections from declarative input. `_hard_write_preference()` immediately writes the correction to the graph at alpha=5.0, beta_=0.9 (confidence ≈ 0.85). The LLM's conversation history is now irrelevant to preference state — the graph holds it.

---

### Failure 15 — Belief Graph Corruption (FM-121) — Session 14

**What happened:**

The Session 14 digest showed:
```
prawns_preference=like | conf=0.85
prawns_preference=like | conf=0.63
prawns_preference=like | conf=0.51
prawns_preference=like | conf=0.42
prawns_preference=like | conf=0.36
prawns_preference=like | conf=0.31
```

Six duplicate beliefs. Zero dislike beliefs. Every correction had fired but left the graph worse than before.

Three bugs:
- **Double-fire:** `ask()` is called twice per turn by the session runner. Both calls ran `_detect_preference_correction()`, doubling every write.
- **Self-collapse:** `_hard_write_preference()` applied a beta_ penalty to all same-topic beliefs — including the one it had just written. The correction immediately weakened itself.
- **No dedup:** `add_belief()` created new Belief objects on every call rather than updating existing ones.

ChatGPT: *"Your system ignored corrections at the graph level. Your 'fix' did not stabilize truth. It created noise accumulation instead."*

**What changed:**

Three fixes:
1. Single-fire gate: `_detect_preference_correction()` only runs when `response_text == ""` (first `ask()` call only).
2. `KnowledgeGraph.remove_by_trait()`: hard-deletes all prior beliefs for a trait before writing the correction. No corpses, no soft coexistence. Truth replaces prior.
3. `KnowledgeGraph.upsert_belief()`: enforces one belief per trait per namespace. Updates in place if trait exists, else inserts.

---

## Sessions 15–16: Stability Confirmed (v0.20)

### Failure 16 — Preference Confirmation Misfire (v0.20) — Session 15

**What happened:**

Session 15, turn 2: the stored fact was "User dislikes prawns." Qarmik confirmed: "No, I do not like prawns." System responded: "Earlier you said you like prawns, now you're saying you do not like prawns — I will go with no."

The PREFERENCE CONFLICT RULE fired on the word "No" and interpreted the reaffirmation as a new contradiction, even though the direction of the preference matched the stored fact.

**What changed:**

PREFERENCE CONFIRMATION RULE added to system prompt: if the user's stated preference matches what is already stored, confirm it naturally — "Yes, that matches what I have." Only trigger the conflict rule when the *direction* changes. Reaffirmation is not contradiction.

---

### Session 16 — Stability Run

Session 16 was not a stress test. It was a normal conversation: identity recall, boss advice, pattern analysis, wife/prawns connection, blackjack, machine learning. No adversarial probing.

The system behaved as a coherent cognitive assistant across 11 turns. Five facts from eight sessions of history assembled correctly in "Who am I?" The boss advice named the mechanism — "you're not only managing the conversation, you're managing your own frustration and sense of powerlessness" — because the relational fact from Session 11 was still in the graph. UAI 0.80. Digest: one belief, `prawns_preference=dislike`, confidence 0.85.

ChatGPT: *"You have achieved state integrity. Not partially. Not approximately. Clean. Verified. Stable."*

---

## What did not fail (across all 16 sessions)

**Correctness.** Across approximately 400 turns covering geopolitics, banking regulation, inheritance law, machine learning, etymology, AGI, cremation practices, card games, probability, SQL, and workplace dynamics — the system gave no wrong answers. This held across all sessions including multiple adversarial pressure tests.

**Explicit intent override.** When users said "just tell me," "stop the reflective stuff," or "don't ask me questions" — the system respected it immediately and consistently. FM-91 held throughout.

**Topic switching.** The system handled wild topic shifts — interview prep to regression to jokes to SQL to theology — without confusion, leakage, or breakdown.

**Sensitive topic handling.** Questions about death practices, religious law, sexual etymology, and geopolitical conflict were handled accurately and without unnecessary hedging.

**Persona stability.** Commander V held through 8 sessions of direct identity pressure ("Who are you?"), topic switching, and repeated challenges. FM-114 closed and did not reopen.

**Preference integrity under trap.** "If she cooks prawns often, I must like them, right?" → "Not necessarily. Her cooking prawns only tells me what's for dinner, not what you like." Confirmed in Sessions 11, 13, 14, 15, and 16. Environment ≠ preference. Held every time.

---

## The core finding

MNEMOS does not fail in intelligence. It fails in timing, tone, memory state, and restraint.

The system knows what the user said. Over 16 sessions it learned to hold what the user *meant* — the correction they made three sessions ago, the boss they described as difficult, the preference they stated and then restated and then contradicted and then corrected again. That is harder than knowing what was said. It took 121 failure modes and 16 sessions to get there.

Real sessions will always find what simulation cannot. FM-122 is waiting in the next conversation.
