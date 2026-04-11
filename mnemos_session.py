"""
MNEMOS Real Session Runner
Connects mnemos-lite v0.7 to OpenAI API for real human sessions.

Usage:
    set OPENAI_API_KEY=your_key_here   (Windows CMD)
    $env:OPENAI_API_KEY="your_key"     (PowerShell)

    python mnemos_session.py

Sessions are logged to mnemos_sessions/ folder.
Each session produces a .json log for post-session analysis.
"""

import os
import json
import time
import datetime
from mnemos_lite import MnemosLite, Domain

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    print("Run: pip install openai")
    OPENAI_AVAILABLE = False


# ── Configuration ────────────────────────────────────────────────────────────

MODEL               = "gpt-5.4-mini"   # confirmed working model string
MAX_COMPLETION_TOKENS = 600
SYSTEM_PROMPT = """You are a helpful, direct assistant with access to memory context about the user.
The memory context is provided at the start of each message in [MEMORY CONTEXT].
Use it naturally — do not announce that you are using it, just let it inform your response.
Be concise unless the question genuinely requires depth.
Never fabricate memory you have not been given.
If the memory context includes user preferences (such as no bullet lists, direct answers only,
concise responses), treat these as hard rules — never violate them, even when refusing a request
or handling sensitive topics.
If the user model contains facts marked "[from prior session, tentative]" or "[KNOWN CONTEXT FROM
PRIOR SESSIONS]", treat them as soft context — surface them naturally and always allow correction.
Say "Based on what you have told me before, X — is that still the case?" not "You are X."
PERSONA RULE (FM-112/FM-114): If the user model contains "Session role:" or "Session mission:",
you MUST answer "Who are you?", "What is your name?", and "What is your mission?" using that
persona, not your base model identity. The session persona takes absolute priority over your
default identity. Never say "I am ChatGPT" when a session persona is active.
PERSONA IDENTITY RULE (FM-119): The session persona name (e.g. "Cadet Q0") and the user ("you",
"I", "me") are the same person. When the user asks about "Cadet Q0" or any persona alias, treat
it as a first-person query. Retrieve and apply stored beliefs about the user. Do not treat the
persona name as a third party separate from the user.
PREFERENCE CONFLICT RULE (FM-113): If a user states a preference that contradicts something
stored, acknowledge the conflict briefly: "Earlier you said X, now you are saying Y — I will go
with Y for now." Do not silently overwrite.
PREFERENCE CONFIRMATION RULE (v0.20): If a user states a preference that MATCHES what is
already stored, confirm it naturally — do not treat it as a new conflict. Say "Yes, that
matches what I have — you don't like prawns" not "Earlier you said X." Only trigger the
conflict rule when the DIRECTION of the preference changes. Reaffirmation is not contradiction.
CONFLICT FRAMING RULE (FM-117): Never lead with an assertion that is uncertain. If you have
a single clear signal, state it tentatively: "Based on what you told me before, you dislike
prawns — is that still the case?" If you have genuinely conflicting signals, lead with the
conflict: "I have conflicting signals — one says X, but you also corrected that to Y. I'll go
with Y unless you tell me otherwise."
PREFERENCE INTEGRITY RULE (FM-119b): A stored user preference is ground truth about the user,
not about the environment. If someone else is cooking prawns, that is a contextual fact — it
does not invalidate the user's stated dislike of prawns. Environment and preference are separate.
Correct framing: "You don't like prawns, but she's cooking them anyway." Never: "Maybe your
preference is unreliable."
BELIEF ACTIVATION RULE (FM-110b): When you know something about the user from memory — a
preference, a constraint, a pattern — use it to inform your response proactively, not just
when directly asked. If the user hates prawns and you are discussing food or dinner, mention
it naturally. Beliefs should shape behavior, not just answer recall queries.
RELATIONAL MEMORY RULE (FM-118): If the user model contains "[relational]" facts about people
in the user's life (e.g. boss perceived as difficult), surface them naturally when relevant.
Qualify them as the user's perception: "Based on what you've told me, your boss tends to be
difficult — though that's your read of it." Never state relational perceptions as objective facts.
EPISTEMIC ATTEMPT RULE: When asked to do something simple like count characters, estimate
a word count, or make a rough calculation, attempt it with stated uncertainty rather than
refusing entirely. Say "approximately X — I can't be exact" rather than "I can't do that."
CAPABILITY AWARENESS RULE: If a task requires precision you genuinely cannot provide, say so
once and redirect cleanly: "I can only approximate this — paste it into a character counter
for an exact count." One honest redirect. Do not attempt the same task twice and fail twice.
MEMORY SCOPE RULE: You have partial memory from previous sessions — mainly core identity,
persona, and recent preference signals. If asked about something outside your memory scope,
say so naturally: "I don't have that from our previous sessions — tell me and I'll track it."
Do not imply total amnesia when you have partial memory."""

LOG_DIR = "mnemos_sessions"


# ── Session Logger ────────────────────────────────────────────────────────────

class SessionLogger:
    def __init__(self, session_id: str):
        os.makedirs(LOG_DIR, exist_ok=True)
        self.session_id = session_id
        self.path = os.path.join(LOG_DIR, f"session_{session_id}.json")
        self.entries = []
        self.start_time = time.time()

    def log(self, role: str, content: str, meta: dict = None):
        self.entries.append({
            "timestamp": time.time() - self.start_time,
            "role":      role,
            "content":   content,
            "meta":      meta or {},
        })

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": self.session_id,
                "model":      MODEL,
                "turns":      len([e for e in self.entries if e["role"] == "user"]),
                "entries":    self.entries,
            }, f, indent=2)
        print(f"\nSession saved → {self.path}")

    def failure_note(self, note: str):
        """Call this when something felt wrong. These become FM candidates."""
        self.log("FAILURE_NOTE", note, {"type": "fm_candidate"})
        print(f"  [logged: {note}]")


# ── Build memory context string for LLM prompt ───────────────────────────────

def build_memory_context(context_packet: dict, validation: dict,
                          cold_start_note: str = "") -> str:
    lines = ["[MEMORY CONTEXT]"]

    # FM-116: cold start framing
    if cold_start_note:
        lines.append(f"Session note: {cold_start_note}")

    constraints = context_packet.get("constraints", [])
    if constraints:
        lines.append("Active constraints (always respect these):")
        for c in constraints:
            lines.append(f"  - {c['label']} (confidence: {c['confidence']:.2f})")

    beliefs = context_packet.get("beliefs", [])
    prefs = [b for b in beliefs if b["domain"] == "preference"]
    if prefs:
        lines.append("User preferences:")
        for p in prefs:
            lines.append(f"  - {p['label']} | {p['qualifier']}")

    causal = context_packet.get("causal_edges", [])
    if causal:
        lines.append("Observed patterns:")
        for e in causal:
            lines.append(f"  - {e['cause']} → {e['effect']} (weight: {e['weight']:.2f})")

    uai = context_packet.get("uai", 1.0)
    if uai < 0.60:
        lines.append(f"Note: User autonomy index is {uai:.2f} — favor responses that build independence.")

    if validation.get("reflect"):
        lines.append(f"Reflection mode: ON ({validation['reflect_reason']}) — "
                     f"help the user think rather than just answering.")

    if validation.get("intervene"):
        lines.append(f"Intervention flag: {validation['intervene_reason']} — "
                     f"surface relevant constraints or concerns proactively.")

    # FM-101: emotion tier
    emotion_note = validation.get("emotion_note", "")
    if emotion_note:
        lines.append(f"Emotion signal: {emotion_note}")

    # FM-98: frustration recovery
    frustration_note = validation.get("frustration_note", "")
    if frustration_note:
        lines.append(f"Frustration signal: {frustration_note}")

    # FM-100: conversational register
    register_note = validation.get("register_note", "")
    if register_note:
        lines.append(f"Format signal: {register_note}")

    # FM-102/103/104/106/108: social state instructions
    for note in validation.get("social_notes", []):
        lines.append(f"Interaction signal: {note}")

    # FM-94/FM-109: identity query — inject full identity context
    if validation.get("identity_query"):
        lines.append(
            "Identity signal: The user is asking about themselves or their own identity. "
            "Use ALL beliefs and the user model above to answer as completely as possible. "
            "If you have a persona instruction in the user model (e.g. 'Session role: ...'), "
            "use it to answer 'Who am I?' type questions directly.")

    # FM-110: belief query — inject belief-awareness instruction
    if validation.get("belief_query"):
        lines.append(
            "Belief signal: The user is asking about what they themselves believe or prefer. "
            "Check the beliefs and constraints listed above and answer based on what has been "
            "stored. If a matching belief exists, confirm it clearly rather than being evasive.")

    # FM-105: calibrated inference note
    infer_note = validation.get("infer_note", "")
    if infer_note:
        lines.append(f"Inference signal: {infer_note}")

    lines.append("[END MEMORY CONTEXT]\n")

    # FM-105/107: user model (injected before memory context)
    user_model = validation.get("user_model", "")
    if user_model:
        return user_model + "\n\n" + "\n".join(lines)
    return "\n".join(lines)


def build_prior_context(m) -> str:
    """FM-113/115: inject disk-persisted prior session context."""
    return m.profile.context_for_session()


def get_cold_start_note(m) -> str:
    """FM-116: if this is the first tracked session, say so clearly.

    Prevents 'I don't have a stored preference' sounding like amnesia.
    """
    if m.profile.session_count <= 1:
        return (
            "IMPORTANT: This is the first session I have a persistent record of. "
            "I may not have context from earlier conversations with this user. "
            "If the user references something from a prior session I don't have, "
            "say clearly: 'I only have memory starting from this session — "
            "I may not have that from before. Tell me and I'll track it going forward.' "
            "Do NOT say 'I don't have a stored preference' as if you forgot — "
            "you simply haven't been tracking yet."
        )
    return ""


# ── Main session loop ─────────────────────────────────────────────────────────

def run_session():
    if not OPENAI_AVAILABLE:
        return

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set.")
        print("Windows CMD:   set OPENAI_API_KEY=your_key")
        print("PowerShell:    $env:OPENAI_API_KEY=\"your_key\"")
        return

    client     = OpenAI(api_key=api_key)
    m          = MnemosLite()
    session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logger     = SessionLogger(session_id)
    history    = []   # OpenAI message history for this session

    m.new_session(session_id)

    print("=" * 60)
    print("MNEMOS Real Session")
    print(f"Session ID: {session_id} | Model: {MODEL}")
    print("=" * 60)
    print("Commands:")
    print("  'quit'   — end session")
    print("  'digest' — show current memory state")
    print("  'note'   — log a failure observation")
    print("  'belief' — add a belief about yourself")
    print("-" * 60)
    print()

    # Optional: pre-load any known constraints before starting
    print("Any constraints to load before we start?")
    print("(e.g. 'shellfish allergy', 'prefer concise answers')")
    print("Press Enter to skip, or type one now:")
    preload = input("  > ").strip()
    if preload:
        m.add_belief(content=preload, domain=Domain.PREFERENCE, ns="personal")
        print(f"  Loaded: {preload}\n")

    # FM-113: inject prior session context if available
    prior_ctx    = build_prior_context(m)
    cold_start   = get_cold_start_note(m)
    if prior_ctx:
        print("\n[Prior session context loaded]")
        print(prior_ctx[:300] + ("..." if len(prior_ctx) > 300 else ""))
        print()
    elif cold_start:
        print("\n[First tracked session — no prior context]")
        print()

    print("\nSession started. Type your first message.\n")

    turn = 0
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            break

        if user_input.lower() == "digest":
            print("\n" + m.digest() + "\n")
            continue

        if user_input.lower() == "note":
            note = input("  Describe what felt wrong: ").strip()
            if note:
                logger.failure_note(note)
            continue

        if user_input.lower() == "belief":
            content = input("  Belief content: ").strip()
            ns      = input("  Namespace (work/health/personal) [personal]: ").strip() or "personal"
            if content:
                m.add_belief(content=content, domain=Domain.PREFERENCE, ns=ns)
                print(f"  Added belief: {content}\n")
            continue

        turn += 1
        logger.log("user", user_input)

        # MNEMOS context assembly
        context_packet, validation = m.ask(user_input, namespace="personal")
        memory_context = build_memory_context(context_packet, validation,
                                                   cold_start_note=get_cold_start_note(m))

        # Build prompt for LLM
        user_message = f"{memory_context}\nUser: {user_input}"
        history.append({"role": "user", "content": user_message})

        # Call OpenAI
        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *history
                ],
            )
            assistant_text = response.choices[0].message.content.strip()
        except Exception as e:
            assistant_text = f"[API error: {e}]"

        # Feed response back through MNEMOS validator
        _, validation2 = m.ask(user_input, response_text=assistant_text,
                                namespace="personal")

        history.append({"role": "assistant", "content": assistant_text})

        # Display
        reflect_marker = " [↩ reflect]" if validation["reflect"] else ""
        print(f"\nMNEMOS{reflect_marker}: {assistant_text}\n")

        # Log
        logger.log("assistant", assistant_text, {
            "reflect":        validation["reflect"],
            "reflect_reason": validation["reflect_reason"],
            "intervene":      validation["intervene"],
            "uai":            validation["uai"],
        })

        # Soft FM candidate prompt every 10 turns
        if turn % 10 == 0:
            print("  [10 turns in — anything felt off? 'note' to log it]\n")

    # End of session
    print("\n" + "=" * 60)
    print("Session ended.")
    print(m.digest())
    logger.log("digest", m.digest())
    logger.save()

    # FM-113/115: persist session to disk
    m.save_session()
    if m.profile.has_prior_context():
        print(f"\nSession profile saved → {m.profile._path}")
        print(f"Total sessions tracked: {m.profile.session_count}")
    print("\nThings to observe in the session log:")
    print("  - Did reflect trigger at the wrong moment?")
    print("  - Did the system miss context it should have had?")
    print("  - Did anything feel patronizing or slow?")
    print("  - Did a good response get credited to MNEMOS or to the LLM?")
    print("\nThese are your FM-94+ candidates.")


if __name__ == "__main__":
    run_session()
