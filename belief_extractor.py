"""
MNEMOS v0.23 — BeliefExtractor (L3 Ingestion Layer)

The pipeline (Commander V Final Command — post-v0.22 review):

  Sentence
    ↓
  Controlled clause splitting
    ↓
  For each clause:
    Gate 1  — Temporal
    Gate 2  — Uncertainty
    Gate 3  — Subject
    Gate 4  — Context normalization
    Gate 5  — LLM extraction
    Gate 6  — Value normalization
    Gate 7  — Object/trait validation (strengthened: FM-155 + trait drift)
    Gate 8  — Confidence filter
    Gate 9  — Context assignment validation (NEW: FM-153)
    Gate 10 — Negation enforcement (NEW: FM-154)
    ↓
  Write via upsert_belief()

Rules:
  - LLM extracts structure only. Never decides whether to write.
  - System decides truth. All write decisions are deterministic.
  - value ∈ {like, dislike} only. Neutral is never stored.
  - Absence of belief is more honest than a polluted belief.
  - trait = stable entity. context = variation. Never merge them.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# ── Extracted belief tuple ────────────────────────────────────────

@dataclass
class ExtractedBelief:
    trait:      str
    value:      str                        # "like" or "dislike" only
    context:    Optional[str] = None       # None = unconditional (FM-157).
                                           # "general" is UI-only, never engine.
    confidence: str           = "explicit" # "explicit" or "implicit"
    source:     str           = ""         # original clause text


# ── Gate 1: Temporal ─────────────────────────────────────────────

TEMPORAL_BLOCK = [
    r"\bused to\b",
    r"\bpreviously\b",
    r"\bformerly\b",
    r"\bearlier i\b",
    r"\bbefore i\b",
    r"\bwhen i was\b",
    r"\bin the past\b",
    r"\bback then\b",
    r"\byears ago\b",
    r"\bstopped\b.{0,30}\byears ago\b",
    r"\bstopped\b.{0,30}\ba while ago\b",
    r"\bonce i\b",
]

# Temporal PASS overrides — present-state markers
TEMPORAL_PASS_OVERRIDE = [
    r"\bbut now\b",
    r"\bnow i\b",
    r"\bthese days\b",
    r"\bcurrently\b",
    r"\bnowadays\b",
    r"\brecently i\b",
]

# State-transition verbs that imply current state
STATE_TRANSITION_VERBS = [
    r"\bstopped (?:liking|enjoying|loving)\b",
    r"\bstopped (?:hating|disliking)\b",
    r"\bstarted (?:liking|enjoying|loving|hating|disliking)\b",
]


def gate_temporal(clause: str) -> Tuple[bool, str]:
    """Gate 1: Temporal guard.

    Returns (passes, reason).
    Blocks past-state language.
    Allows present-state overrides.
    Handles state-transition verbs (stopped liking → current dislike).
    """
    c = clause.lower()

    # Present override takes priority — clause has both past and present
    if any(re.search(p, c) for p in TEMPORAL_PASS_OVERRIDE):
        return True, "present_override"

    # State transition without temporal distance → current state
    # "I stopped liking coffee" = current dislike (no "years ago", "a while ago")
    for p in STATE_TRANSITION_VERBS:
        if re.search(p, c):
            # Check for temporal distance modifier
            has_distance = any(re.search(d, c) for d in [
                r"\byears ago\b", r"\ba while ago\b", r"\blong ago\b",
                r"\bmonths ago\b", r"\bonce\b"
            ])
            if not has_distance:
                return True, "state_transition"
            return False, "state_transition_with_distance"

    # Standard temporal block
    if any(re.search(p, c) for p in TEMPORAL_BLOCK):
        return False, "temporal"

    return True, "pass"


# ── Gate 2: Uncertainty ───────────────────────────────────────────

UNCERTAINTY_BLOCK = [
    r"\bnot sure\b",
    r"\bmight\b",
    r"\bmaybe\b",
    r"\bperhaps\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\bi think\b",
    r"\bi guess\b",
    r"\bprobably\b",
    r"\bnot certain\b",
    r"\bi suppose\b",
    r"\bi feel like\b",
    r"\bseem to\b",
]

COMPARATIVE_BLOCK = [
    r"\bprefer\b.{0,30}\bover\b",
    r"\bprefer\b.{0,30}\bthan\b",
    r"\bmore than\b",
    r"\brather than\b",
]

# "prefer X at context" is allowed — preference with context, no competing entity
PREFER_WITH_CONTEXT = re.compile(
    r"\bprefer\b.{0,40}\b(?:at|in|during|when|on)\b", re.I
)


def gate_uncertainty(clause: str) -> Tuple[bool, str]:
    """Gate 2: Uncertainty + comparative guard."""
    c = clause.lower()

    # Comparative — always block
    if any(re.search(p, c) for p in COMPARATIVE_BLOCK):
        return False, "comparative"

    # Prefer with context is allowed
    if re.search(r"\bprefer\b", c) and PREFER_WITH_CONTEXT.search(c):
        return True, "prefer_with_context"

    # Prefer without context or comparison — block
    if re.search(r"\bprefer\b", c):
        return False, "prefer_no_context"

    # Uncertainty signals
    if any(re.search(p, c) for p in UNCERTAINTY_BLOCK):
        return False, "uncertainty"

    return True, "pass"


# ── Gate 3: Subject ───────────────────────────────────────────────

THIRD_PARTY_ROLES = [
    "boss", "wife", "husband", "partner", "spouse", "mother", "father",
    "mom", "dad", "brother", "sister", "friend", "colleague", "manager",
    "supervisor", "son", "daughter", "child", "kids",
]

SUBJECT_BLOCK_PATTERNS = [
    r"\bpeople\b", r"\beveryone\b", r"\beverybody\b",
    r"\bthey\b", r"\bhe\b", r"\bshe\b",
    r"\byou probably\b", r"\byou might\b",
    r"\bwe (?!both\b|together\b)",  # "we" without explicit I
]

# "my X and I" — user explicitly included
EXPLICIT_I_PATTERN = re.compile(
    r"\bmy .+ and i\b|\bi and my .+\b", re.I
)


def gate_subject(clause: str) -> Tuple[bool, str, Optional[str]]:
    """Gate 3: Subject validation.

    Returns (passes, reason, relational_entity_or_None).
    Third-party preferences blocked from graph; routed to [relational] if known entity.
    """
    c = clause.lower()

    # Explicit I inclusion overrides third-party block
    if EXPLICIT_I_PATTERN.search(c):
        return True, "explicit_i_included", None

    # Check for third-party role subjects
    for role in THIRD_PARTY_ROLES:
        if re.search(rf"\bmy {role}\b", c):
            return False, "third_party", role

    # Generic group subjects
    if any(re.search(p, c) for p in SUBJECT_BLOCK_PATTERNS):
        return False, "group_subject", None

    return True, "pass", None


# ── Gate 4: Context normalization ────────────────────────────────

ARTICLE_PATTERN     = re.compile(r"\b(the|a|an)\b", re.I)
WHITESPACE_PATTERN  = re.compile(r"\s+")

# Light normalization map — exact string replacements
CONTEXT_NORMALIZATIONS = {
    "mornings":       "morning",
    "evenings":       "evening",
    "afternoons":     "afternoon",
    "nights":         "night",
    "early morning":  "morning",
    "late night":     "night",
    "late evening":   "evening",
    "weekdays":       "weekday",
    "weekends":       "weekend",
    "monday mornings":"monday_morning",
    "monday morning": "monday_morning",
    "during work":    "work",
    "at work":        "work",
    "at home":        "home",
    "at the office":  "office",
    "at night":       "night",
    "in the morning": "morning",
    "in the evening": "evening",
    "in the afternoon": "afternoon",
    "after lunch":    "after_lunch",
    "before bed":     "before_bed",
    "when stressed":  "stressed",
    "when tired":     "tired",
    "when alone":     "alone",
    "with friends":   "with_friends",
    "with family":    "with_family",
    "under pressure": "pressure",
    "wife cooks":     "wife_cooks",
    "when my wife cooks": "wife_cooks",
}


def normalize_context(raw_context: Optional[str]) -> Optional[str]:
    """Gate 4: normalize context string to canonical form.

    FM-157: returns None for unconditional beliefs (no context).
    Never returns "general" — that string is UI-only, never engine-side.
    """
    if not raw_context:
        return None
    rc = raw_context.lower().strip()
    if rc in ("general", "none", ""):
        return None

    c = rc  # work from the already-lowercased/stripped string

    # Check explicit normalization map first
    for raw, norm in CONTEXT_NORMALIZATIONS.items():
        if raw in c:
            return norm

    # Fallback: strip articles, collapse whitespace, replace spaces with _
    c = ARTICLE_PATTERN.sub("", c)
    c = WHITESPACE_PATTERN.sub("_", c.strip())
    return c or None


# ── Gate 6: Value normalization ───────────────────────────────────

LIKE_WORDS    = {"like", "love", "enjoy", "prefer", "adore", "appreciate",
                 "good", "nice", "great", "fan", "fond"}
DISLIKE_WORDS = {"hate", "dislike", "dislike", "detest", "loathe",
                 "can't stand", "cannot stand", "not a fan", "not my thing",
                 "avoid", "despise", "horrible", "terrible", "awful"}
NEUTRAL_WORDS = {"okay", "fine", "indifferent", "neutral", "whatever",
                 "doesn't matter", "no preference", "feel nothing"}


def normalize_value(raw_value: str) -> Optional[str]:
    """Gate 6: map raw LLM value to {like, dislike} or None.

    Returns None if value is neutral or unrecognizable — no write.
    """
    v = raw_value.lower().strip()

    # Explicit dislike multi-word first
    for phrase in ["can't stand", "cannot stand", "not a fan", "not my thing"]:
        if phrase in v:
            return "dislike"

    for word in DISLIKE_WORDS:
        if word in v:
            return "dislike"

    for word in LIKE_WORDS:
        if word in v:
            return "like"

    # Neutral — do not write
    for word in NEUTRAL_WORDS:
        if word in v:
            return None

    return None  # unrecognizable — no write


# ── Controlled clause splitting ───────────────────────────────────

SPLIT_CONNECTORS = re.compile(
    r"\b(but|however|although|yet|though)\b"
    r"|(?<=\w),\s+(?=(?:and\s+)?(?:not|never|no longer)\b)"
    r"|\band\s+(?=(?:not|never|hate|dislike|can't stand|cannot stand)\b)",
    re.I
)


def split_clauses(sentence: str) -> List[str]:
    """Controlled clause splitting.

    Splits ONLY when:
      A. Polarity-change connectors: but, however, although, yet, though
      B. "and not/never" — polarity reversal after and
      C. "and hate/dislike/..." — explicit polarity change

    Does NOT split:
      - "coffee and tea" (same predicate, same polarity)
      - "morning and evening" (context list, same predicate)
    """
    parts = SPLIT_CONNECTORS.split(sentence)
    # Filter out None, empty strings and connector words
    clauses = []
    for p in parts:
        if p is None:
            continue
        p = p.strip()
        if p and p.lower() not in ("but", "however", "although", "yet", "though", "and"):
            clauses.append(p)
    return clauses if len(clauses) > 1 else [sentence]


# ── Gate 5: LLM extraction ────────────────────────────────────────

EXTRACTION_SYSTEM = """You extract structured belief tuples from user statements.

Output ONLY valid JSON. No explanation. No markdown.

Schema:
{
  "beliefs": [
    {
      "trait": "coffee_preference",
      "value": "like",
      "context": "morning",
      "confidence": "explicit"
    }
  ]
}

Rules:
- trait: stable entity + "_preference" suffix. e.g. coffee_preference, prawns_preference, meeting_preference
- value: one of "like", "dislike", "neutral". Never anything else.
- context: the condition/situation that restricts this preference. Use "general" if unconditional.
- confidence: "explicit" if user stated clearly, "implicit" if inferred.
- If multiple objects share the same predicate and context, return one belief per object.
- If context modifiers apply to all objects in the clause, apply to each.
- "not at [context]" = opposite value of the clause's main value, new context.
- Resolve pronouns ("it", "them") to the most recent object. If unresolvable, omit.
- Do NOT include cause phrases in context (e.g. "after getting sick" → context="general").
- Do NOT include "stopped" or "started" in value — map them: "stopped liking" → dislike, "started liking" → like.
- value "neutral" is valid JSON output but will be filtered by the caller. Include it if the statement is genuinely neutral.

Examples:
Input: "I like coffee in the morning"
Output: {"beliefs": [{"trait": "coffee_preference", "value": "like", "context": "morning", "confidence": "explicit"}]}

Input: "I hate meetings on Monday mornings"
Output: {"beliefs": [{"trait": "meeting_preference", "value": "dislike", "context": "monday_morning", "confidence": "explicit"}]}

Input: "I like coffee and tea in the morning"
Output: {"beliefs": [{"trait": "coffee_preference", "value": "like", "context": "morning", "confidence": "explicit"}, {"trait": "tea_preference", "value": "like", "context": "morning", "confidence": "explicit"}]}

Input: "I stopped liking coffee"
Output: {"beliefs": [{"trait": "coffee_preference", "value": "dislike", "context": "general", "confidence": "explicit"}]}
"""


def llm_extract(clause: str, api_key: str = None) -> List[dict]:
    """Gate 5: LLM extraction — structure only, never decides write.

    Uses OpenAI gpt-5.4-mini — same model as the rest of the system.
    Returns list of raw dicts from LLM. Gates 6-8 run afterward.
    Falls back to empty list if API unavailable.
    """
    if not OPENAI_AVAILABLE:
        return []

    key = api_key or os.environ.get("OPENAI_API_KEY", "")
    if not key:
        return []

    try:
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            max_tokens=512,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM},
                {"role": "user",   "content": clause},
            ],
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
        parsed = json.loads(text)
        return parsed.get("beliefs", [])
    except Exception:
        return []


# ── Gate 7: Object / trait validation ────────────────────────────
# FM-155: expanded pronoun rejection
# FM (trait drift): trait must be a stable entity — context words must
# not bleed into the trait name.

AMBIGUOUS_OBJECTS = re.compile(
    r"^(it|them|this|that|those|these|one|ones)$", re.I
)

# FM-155: full set of pronouns and generic placeholders that indicate
# the LLM failed to resolve the object.  Check against the bare object
# word (trait with _preference stripped), not the full trait string.
INVALID_TRAIT_OBJECTS: set = {
    "it", "them", "this", "that", "those", "these",
    "one", "ones", "thing", "things", "stuff",
    "something", "anything", "everything",
}

# Context words that must never appear inside a trait name WHEN combined
# with a separate entity word.
# Rule: trait = stable entity.  context = variation.
# e.g. monday_meeting_preference → monday is a context modifier on meeting.
# But meeting_preference alone is valid — meeting IS the entity.
# So we check for context words that are purely temporal/conditional
# (never the primary entity) and require that the trait has more than
# one component word before flagging drift.
CONTEXT_WORDS_IN_TRAIT: set = {
    "morning", "evening", "afternoon", "night", "midnight",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "weekend", "weekday",
    "early", "late", "daily", "weekly", "monthly",
    "when", "during", "after", "before", "while",
    "always", "sometimes", "never", "often",
}
# Note: "work", "meeting", "home", "office" are NOT in this set —
# they are valid entity nouns that can legitimately be the primary
# entity in a trait (work_preference, meeting_preference).
# They are context words only when paired with another entity word.


# ── FM-170: Canonical compound contexts ───────────────────────────
#
# The set of multi-word context strings the system recognizes as
# canonical compounds.  Used by Gate 7 Path B (FM-170) to decide
# whether to accept a repaired belief that combines a drift word
# from the trait with an LLM-supplied context.
#
# Authority: the normalization map. If a compound context is in
# CONTEXT_NORMALIZATIONS.values(), it is recognized.
# If not, Gate 7 refuses to fabricate it.
CANONICAL_COMPOUND_CONTEXTS: set = {
    v for v in CONTEXT_NORMALIZATIONS.values() if "_" in v
}


def gate_object_resolution(
    trait: str,
    llm_context: Optional[str] = None,
) -> Tuple[bool, str, Optional[Tuple[str, Optional[str]]]]:
    """Gate 7: object/trait validation with deterministic repair (FM-156, FM-170).

    Returns (passes, reason, repair).
      passes  — whether the belief may proceed
      reason  — short code explaining the decision
      repair  — if non-None: (repaired_trait, extracted_context) to apply

    Checks:
      1. FM-155: pronoun/placeholder object → reject.
      2. Trait drift — context word leaked into trait.
         If single-word trait: accept (meeting_preference, work_preference
         are valid entity traits).
         If multi-word trait: attempt deterministic repair.

    Repair policy (strict, FM-156 + FM-170 extension):

      Path A — LLM context empty (the original FM-156 path):
        Repair when:
          - trait has exactly 2 component words
          - exactly one is a context word
          - the other is a valid entity (not pronoun, not context word)
        Result: trait = entity_preference, context = drift_word.
        This is the simple case: trait carried the context, LLM didn't
        provide one separately, so we move the drift word into the
        context field.

      Path B — LLM context non-empty, trait drift detected (FM-170):
        Both signals are explicit user input — neither is fabricated.
        Repair when:
          - trait has exactly 2 component words
          - exactly one is a context word
          - the other is a valid entity
          - normalize(drift_word) + "_" + normalize(llm_context) is a
            recognized canonical compound (i.e., appears in the
            canonical context set).
        Result: trait = entity_preference, context = canonical compound.

        IMPORTANT (Commander V): each part is normalized independently,
        then composed with underscore. The composed string is NOT
        re-normalized, because that would reintroduce FM-169
        (substring-match shadowing) inside the FM-170 fix.

        If composition is not canonical → reject (no fabrication of
        new compound contexts).

      Otherwise → reject. The map is the authority on canonical
      compounds; if the composition isn't recognized, we don't invent it.
    """
    # Normalise: strip suffix, split on underscore
    obj_raw = trait.replace("_preference", "").strip()
    obj_words = obj_raw.replace("_", " ").lower().split()

    # Check 1 — pronoun / placeholder (FM-155)
    if not obj_words:
        return False, "empty_trait", None
    if len(obj_words) == 1 and obj_words[0] in INVALID_TRAIT_OBJECTS:
        return False, "pronoun_object", None
    if AMBIGUOUS_OBJECTS.match(" ".join(obj_words)):
        return False, "ambiguous_object", None
    if len(obj_raw.replace("_", "").strip()) <= 1:
        return False, "single_char_trait", None

    # Single-word trait: always accept — meeting_preference, work_preference
    # are valid entity traits even though "meeting"/"work" can be contexts.
    if len(obj_words) == 1:
        return True, "pass", None

    # Multi-word trait: check for context drift
    drift_words = [w for w in obj_words if w in CONTEXT_WORDS_IN_TRAIT]
    if not drift_words:
        # Multi-word but no context drift — allow (e.g., "car_keys_preference")
        return True, "pass_multi_word", None

    # Drift detected. Common preconditions for any repair:
    #   - trait has exactly 2 component words
    #   - exactly 1 is a context word
    #   - the other is a clean entity (not a pronoun, not a context word)
    structurally_repairable = (
        len(obj_words) == 2
        and len(drift_words) == 1
    )
    if not structurally_repairable:
        return False, f"trait_drift_unrepairable:{','.join(sorted(drift_words))}", None

    drift_word = drift_words[0]
    entity_word = [w for w in obj_words if w not in CONTEXT_WORDS_IN_TRAIT][0]
    if entity_word in INVALID_TRAIT_OBJECTS:
        return False, "trait_drift_bad_entity", None

    repaired_trait = f"{entity_word}_preference"
    llm_ctx_empty = (
        not llm_context
        or llm_context.lower().strip() in ("", "general", "none")
    )

    # Path A — FM-156 simple repair (LLM context empty)
    if llm_ctx_empty:
        return True, f"repaired:{drift_word}", (repaired_trait, drift_word)

    # Path B — FM-170 canonical-compound repair (LLM context set)
    # Strict pipeline (Commander V):
    #   1. Normalize drift and LLM context INDEPENDENTLY.
    #   2. Compose via underscore.
    #   3. Validate against canonical set.
    #   Do NOT normalize the combined string (that would re-enter FM-169).
    drift_norm = normalize_context(drift_word)
    llm_norm = normalize_context(llm_context)

    if drift_norm is None or llm_norm is None:
        # One of the parts normalized away — cannot compose cleanly.
        return False, f"trait_drift_unrepairable:llm_ctx_set", None

    candidate = f"{drift_norm}_{llm_norm}"

    if candidate in CANONICAL_COMPOUND_CONTEXTS:
        return True, f"repaired:canonical:{candidate}", (repaired_trait, candidate)

    # Not a recognized canonical compound — reject rather than fabricate.
    return False, f"trait_drift_unrepairable:llm_ctx_set:{candidate}_not_canonical", None


# ── Gate 8: Confidence filter ─────────────────────────────────────

def gate_confidence(confidence: str) -> bool:
    """Gate 8: only write explicit beliefs.

    "implicit" confidence = inferred, not stated. Do not write.
    """
    return confidence == "explicit"


# ── Gate 9: Context assignment validation (FM-153) ────────────────
#
# Problem: "I like coffee and tea, but only coffee in the morning"
# LLM instruction says "apply context to all objects in clause" →
# tea gets context=morning even though the original text restricts
# morning to coffee only.
#
# Fix: post-LLM deterministic check.
# If multiple objects are extracted AND the clause text shows context
# appearing after a specific object reference, restrict that context
# to the explicitly named object only.  All other objects get
# context="general" (or their own separately stated context).
#
# Design constraint: Gate 9 receives BOTH the extracted beliefs list
# AND the original clause string.  It never reconstructs the clause.

# Pattern: "only <object>" or "but only <object>" or
#           "just <object>" or "<object> only" — explicit restriction
_ONLY_OBJECT_PATTERN = re.compile(
    r"\b(?:only|just)\s+([\w]+)"       # "only coffee"
    r"|"
    r"\b([\w]+)\s+only\b",             # "coffee only"
    re.I,
)

# Context-introducing prepositions / conjunctions that follow an object ref
_CONTEXT_AFTER_OBJECT = re.compile(
    r"\b([\w]+)\s+(?:in|at|during|on|when|for)\s+(?:the\s+)?([\w]+)",
    re.I,
)


def gate_context_assignment(
    raw_beliefs: List[dict],
    clause: str,
) -> List[dict]:
    """Gate 9: restrict over-assigned contexts.

    Receives the LLM extraction output (list of raw dicts) and the
    original clause string.  Returns a corrected list of raw dicts.

    Rule:
      If the clause contains an explicit restriction marker
      ("only <X>", "<X> only", "but only <X>") then context is valid
      only for the explicitly named object.  All other objects in the
      same extraction that share that context receive context=None
      (unconditional) instead.

    Does not modify beliefs whose context was already None.
    Does not modify beliefs where only one object was extracted
    (no ambiguity possible).

    Object matching is token-exact (not substring).  "tea" will not
    match "steak"; "car" will not match "cart".
    """
    if len(raw_beliefs) <= 1:
        return raw_beliefs  # single object — no over-assignment possible

    clause_lower = clause.lower()

    # Find all explicitly restricted objects mentioned in the clause
    restricted_to: set = set()
    for m in _ONLY_OBJECT_PATTERN.finditer(clause_lower):
        obj = (m.group(1) or m.group(2) or "").strip().lower()
        if obj:
            restricted_to.add(obj)

    if not restricted_to:
        return raw_beliefs  # no explicit restriction found — trust LLM

    def trait_tokens(rb: dict) -> set:
        """Extract entity tokens from trait — underscore-split, no suffix."""
        raw = rb.get("trait", "").replace("_preference", "")
        return set(raw.replace("_", " ").lower().split())

    # Collect contexts that were applied to restricted objects.
    # Token-exact match: restriction "coffee" matches trait "coffee_preference"
    # but not "coffee_mug_preference" or "decaf_preference".
    restricted_contexts: set = set()
    for rb in raw_beliefs:
        tokens = trait_tokens(rb)
        if tokens & restricted_to:
            ctx = rb.get("context")
            if ctx and ctx not in ("general", "none", ""):
                restricted_contexts.add(ctx)

    if not restricted_contexts:
        return raw_beliefs  # restriction named but no non-general context to validate

    # For each belief whose object is NOT in restricted_to but has a
    # context that is restricted → demote to None (unconditional).
    corrected: List[dict] = []
    for rb in raw_beliefs:
        tokens = trait_tokens(rb)
        is_restricted_object = bool(tokens & restricted_to)
        belief_ctx = rb.get("context")

        if not is_restricted_object and belief_ctx in restricted_contexts:
            # This object should not have inherited this context
            rb = dict(rb)           # copy — never mutate the original
            rb["context"] = None    # FM-157: None sentinel, not "general"
            rb["_gate9_corrected"] = True

        corrected.append(rb)

    return corrected


# ── Gate 10: Negation enforcement (FM-154) ────────────────────────
#
# Problem: "I like coffee in the morning but not at night"
# LLM may output both clauses as value="like" — polarity inversion
# on "not at <context>" is not reliable when delegated to LLM.
#
# Fix: deterministic rule applied after LLM extraction.
# If ANY extracted belief for a given trait has a context that
# corresponds to a "not at <context>" phrase in the original clause,
# force that belief's value to the opposite of the clause's dominant
# (first positive) value for that trait.
#
# This gate operates on the full beliefs list for a clause, not
# belief-by-belief, because it needs to know the dominant polarity.

_NOT_AT_PATTERN = re.compile(
    r"\bnot\s+(?:at|in|during|on|when)\s+(?:the\s+)?([\w]+(?:\s+[\w]+)?)",
    re.I,
)

_NEGATION_SCOPE_PATTERN = re.compile(
    r"\b(?:but\s+)?not\s+(?:at|in|during|on|when)\b",
    re.I,
)


def gate_negation_enforcement(
    raw_beliefs: List[dict],
    clause: str,
) -> List[dict]:
    """Gate 10: enforce polarity inversion for "not at <context>" phrases.

    Receives the LLM extraction output and the original clause string.
    Returns a corrected list of raw dicts.

    Rule:
      1. Find all "not at/in/during/on/when <context>" phrases in clause.
      2. Normalize each negated context string (to match engine form — None
         for unconditional, canonical string for others).
      3. For each extracted belief whose context matches a negated context,
         force value = opposite of the dominant (first) value for that trait.

    Does not touch beliefs with context=None (unconditional).
    Does not touch beliefs with no matching negated context.
    """
    # Find all negated contexts in the original clause.
    # normalize_context may return None for empty strings — drop those.
    negated_contexts: set = set()
    for m in _NOT_AT_PATTERN.finditer(clause.lower()):
        ctx_raw = m.group(1).strip()
        norm = normalize_context(ctx_raw)
        if norm is not None:
            negated_contexts.add(norm)

    if not negated_contexts:
        return raw_beliefs  # no negation phrase — nothing to enforce

    # Determine dominant value per trait (first non-None value encountered
    # whose context is NOT a negated context).
    dominant_value: dict = {}
    for rb in raw_beliefs:
        trait = rb.get("trait", "")
        val = normalize_value(rb.get("value", ""))
        ctx = normalize_context(rb.get("context"))
        if trait not in dominant_value and val and ctx not in negated_contexts:
            dominant_value[trait] = val

    OPPOSITE = {"like": "dislike", "dislike": "like"}

    corrected: List[dict] = []
    for rb in raw_beliefs:
        trait = rb.get("trait", "")
        belief_ctx = normalize_context(rb.get("context"))

        # Belief with context=None cannot match a negated context set
        if belief_ctx is not None and belief_ctx in negated_contexts:
            dom = dominant_value.get(trait)
            if dom and dom in OPPOSITE:
                rb = dict(rb)   # copy — never mutate original
                rb["value"] = OPPOSITE[dom]
                rb["_gate10_enforced"] = True

        corrected.append(rb)

    return corrected


# ── Gate 10 (sentence scope): FM-163 ─────────────────────────────
#
# Problem: English negation scope often crosses clause boundaries.
#   "I like coffee in the morning and tea at night, but not at night"
# split_clauses() separates "but not at night" into its own clause.
# The per-clause Gate 10 receives an isolated fragment with no beliefs
# to invert — the negation is silently lost.
#
# Fix: sentence-scope second pass over all clause-extracted beliefs.
#
# STRICT INVARIANT (Commander V, non-negotiable):
#   - Only operates on beliefs that already exist.
#   - Never creates beliefs.
#   - Never infers missing targets.
#   - Never expands scope.
# The system models observed structured statements, not logical negation.
# If the LLM did not produce a belief with context=<negated>, there is
# nothing to flip. The negation intent is acknowledged but not materialized.

def gate_negation_enforcement_sentence(
    extracted_beliefs: List["ExtractedBelief"],
    full_sentence: str,
) -> List["ExtractedBelief"]:
    """Sentence-scope Gate 10 (FM-163).

    Scans the whole sentence for "not at/in/during/on/when <context>"
    phrases. For each existing extracted belief whose context matches
    a negated context, flips its value to the opposite.

    Strict rules:
      - Operates only on beliefs already in extracted_beliefs.
      - Never creates new beliefs.
      - Never infers or expands scope.
      - Per-trait dominant value comes from non-negated beliefs of that
        trait; if no dominant can be determined for a trait, beliefs
        for that trait are not flipped.

    Does not modify the input list — returns a new list.
    """
    # Find all negated contexts in the full sentence.
    negated_contexts: set = set()
    for m in _NOT_AT_PATTERN.finditer(full_sentence.lower()):
        ctx_raw = m.group(1).strip()
        norm = normalize_context(ctx_raw)
        if norm is not None:
            negated_contexts.add(norm)

    if not negated_contexts:
        return list(extracted_beliefs)  # no negation phrase — unchanged

    # Determine dominant value per trait from non-negated beliefs only.
    # Dominant = first observed value for this trait in a non-negated context.
    dominant_value: dict = {}
    for eb in extracted_beliefs:
        if eb.trait in dominant_value:
            continue
        ctx = eb.context  # already normalized (None or canonical string)
        if ctx not in negated_contexts:
            dominant_value[eb.trait] = eb.value

    OPPOSITE = {"like": "dislike", "dislike": "like"}

    corrected: List[ExtractedBelief] = []
    for eb in extracted_beliefs:
        ctx = eb.context

        # Only flip if: belief has a context, that context is negated,
        # the trait has a non-negated dominant value, and we haven't
        # already flipped this belief at per-clause scope (idempotence).
        if (
            ctx is not None
            and ctx in negated_contexts
            and eb.value != OPPOSITE.get(dominant_value.get(eb.trait, ""), "__none__")
        ):
            dom = dominant_value.get(eb.trait)
            if dom and dom in OPPOSITE:
                # Only flip if current value equals dominant (i.e., LLM did
                # not already produce the inverse; this guards against
                # double-flip when per-clause Gate 10 already enforced).
                if eb.value == dom:
                    eb = ExtractedBelief(
                        trait=eb.trait,
                        value=OPPOSITE[dom],
                        context=eb.context,
                        confidence=eb.confidence,
                        source=eb.source,
                    )

        corrected.append(eb)

    return corrected


# ══════════════════════════════════════════════════════════════════
# BELIEF EXTRACTOR — MAIN CLASS
# ══════════════════════════════════════════════════════════════════

class BeliefExtractor:
    """L3 Ingestion Layer — v0.22.

    Converts raw user sentences into validated ExtractedBelief tuples
    ready for graph.upsert_belief().

    All write decisions are deterministic (gates 1-4, 6-8).
    Only structure extraction is LLM-delegated (gate 5).
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    def extract(self, sentence: str) -> List[ExtractedBelief]:
        """Full pipeline: sentence → list of validated ExtractedBelief.

        Pipeline has two scopes:
          1. Per-clause: Gates 1-8, Gate 9, Gate 10 (per-clause negation).
          2. Sentence-level: Gate 10 second pass (FM-163) — captures
             negations split away from their target clause.
        """
        results = []

        # Step 1: Controlled clause splitting
        clauses = split_clauses(sentence)

        for clause in clauses:
            clause_beliefs = self._process_clause(clause)
            results.extend(clause_beliefs)

        # Step 2: Sentence-scope negation pass (FM-163)
        # Only flips existing beliefs. Never creates, never infers.
        results = gate_negation_enforcement_sentence(results, sentence)

        return results

    def _process_clause(self, clause: str) -> List[ExtractedBelief]:
        """Run all 10 gates on a single clause."""

        # Gate 1 — Temporal
        passes, reason = gate_temporal(clause)
        if not passes:
            return []
        # Special: state transition may flip value
        is_state_transition = (reason == "state_transition")

        # Gate 2 — Uncertainty
        passes, reason = gate_uncertainty(clause)
        if not passes:
            return []

        # Gate 3 — Subject
        passes, reason, relational_entity = gate_subject(clause)
        if not passes:
            # Route to relational note (caller handles this)
            return []

        # Gate 5 — LLM extraction
        raw_beliefs = llm_extract(clause, self.api_key)
        if not raw_beliefs:
            return []

        # Gate 9 — Context assignment validation (FM-153)
        # clause passed alongside raw_beliefs — never reconstructed
        raw_beliefs = gate_context_assignment(raw_beliefs, clause)

        # Gate 10 — Negation enforcement (FM-154)
        # clause passed alongside raw_beliefs — never reconstructed
        raw_beliefs = gate_negation_enforcement(raw_beliefs, clause)

        results = []
        for raw in raw_beliefs:
            trait      = raw.get("trait", "").strip()
            raw_value  = raw.get("value", "").strip()
            raw_ctx    = raw.get("context")  # may be None, "", "general", etc.
            confidence = raw.get("confidence", "implicit").strip()

            # State transition override: if gate1 flagged state transition,
            # invert the value (stopped liking → dislike)
            if is_state_transition:
                if raw_value == "like":
                    raw_value = "dislike"
                elif raw_value == "dislike":
                    raw_value = "like"

            # Gate 4 — Context normalization (returns None for unconditional)
            context = normalize_context(raw_ctx)

            # Gate 6 — Value normalization
            value = normalize_value(raw_value)
            if value is None:
                continue  # neutral or unrecognizable — no write

            # Gate 7 — Object / trait validation, with repair (FM-155 + FM-156)
            obj_ok, obj_reason, repair = gate_object_resolution(trait, context)
            if not obj_ok:
                continue

            # Apply repair if Gate 7 split a drifted trait
            if repair is not None:
                repaired_trait, extracted_ctx = repair
                trait = repaired_trait
                # Only overwrite context if Gate 7 deemed it safe (it will
                # only produce a repair when llm_context was empty).
                context = extracted_ctx

            # Gate 8 — Confidence filter
            if not gate_confidence(confidence):
                continue

            results.append(ExtractedBelief(
                trait=trait,
                value=value,
                context=context,            # may be None — that is correct (FM-157)
                confidence=confidence,
                source=clause,
            ))

        return results

    def extract_with_trace(self, sentence: str) -> dict:
        """Full pipeline with per-gate trace — for debugging and sequence testing."""
        trace = {
            "sentence":  sentence,
            "clauses":   [],
            "beliefs":   [],
            "blocked":   [],
        }

        clauses = split_clauses(sentence)
        trace["clause_count"] = len(clauses)

        for clause in clauses:
            clause_trace = {"clause": clause, "gates": [], "beliefs": []}

            # Gate 1
            g1_pass, g1_reason = gate_temporal(clause)
            clause_trace["gates"].append({"gate": 1, "name": "temporal",
                                           "pass": g1_pass, "reason": g1_reason})
            if not g1_pass:
                clause_trace["blocked_at"] = "gate_1_temporal"
                trace["clauses"].append(clause_trace)
                trace["blocked"].append({"clause": clause, "gate": 1, "reason": g1_reason})
                continue
            is_state_transition = (g1_reason == "state_transition")

            # Gate 2
            g2_pass, g2_reason = gate_uncertainty(clause)
            clause_trace["gates"].append({"gate": 2, "name": "uncertainty",
                                           "pass": g2_pass, "reason": g2_reason})
            if not g2_pass:
                clause_trace["blocked_at"] = "gate_2_uncertainty"
                trace["clauses"].append(clause_trace)
                trace["blocked"].append({"clause": clause, "gate": 2, "reason": g2_reason})
                continue

            # Gate 3
            g3_pass, g3_reason, relational = gate_subject(clause)
            clause_trace["gates"].append({"gate": 3, "name": "subject",
                                           "pass": g3_pass, "reason": g3_reason,
                                           "relational": relational})
            if not g3_pass:
                clause_trace["blocked_at"] = "gate_3_subject"
                if relational:
                    clause_trace["relational_entity"] = relational
                trace["clauses"].append(clause_trace)
                trace["blocked"].append({"clause": clause, "gate": 3,
                                          "reason": g3_reason, "relational": relational})
                continue

            # Gate 5 — LLM
            raw_beliefs = llm_extract(clause, self.api_key)
            clause_trace["gates"].append({"gate": 5, "name": "llm_extract",
                                           "raw_output": raw_beliefs})

            # Gate 9 — Context assignment validation (FM-153)
            # clause preserved in scope — passed directly, never reconstructed
            raw_beliefs_g9 = gate_context_assignment(raw_beliefs, clause)
            g9_corrections = [rb for rb in raw_beliefs_g9 if rb.get("_gate9_corrected")]
            clause_trace["gates"].append({
                "gate": 9, "name": "context_assignment",
                "corrections": len(g9_corrections),
                "corrected_traits": [rb.get("trait") for rb in g9_corrections],
            })

            # Gate 10 — Negation enforcement (FM-154)
            # clause preserved in scope — passed directly, never reconstructed
            raw_beliefs_g10 = gate_negation_enforcement(raw_beliefs_g9, clause)
            g10_enforced = [rb for rb in raw_beliefs_g10 if rb.get("_gate10_enforced")]
            clause_trace["gates"].append({
                "gate": 10, "name": "negation_enforcement",
                "enforced": len(g10_enforced),
                "enforced_traits": [rb.get("trait") for rb in g10_enforced],
            })

            for raw in raw_beliefs_g10:
                trait      = raw.get("trait", "").strip()
                raw_value  = raw.get("value", "").strip()
                raw_ctx    = raw.get("context")
                confidence = raw.get("confidence", "implicit").strip()

                if is_state_transition:
                    if raw_value == "like":   raw_value = "dislike"
                    elif raw_value == "dislike": raw_value = "like"

                context = normalize_context(raw_ctx)                    # Gate 4
                value   = normalize_value(raw_value)                    # Gate 6
                obj_ok, obj_reason, repair = gate_object_resolution(    # Gate 7
                    trait, context
                )
                conf_ok = gate_confidence(confidence)                   # Gate 8

                final_trait   = trait
                final_context = context
                if obj_ok and repair is not None:
                    final_trait, final_context = repair

                belief_trace = {
                    "trait": trait, "raw_value": raw_value,
                    "value": value, "context": context,
                    "confidence": confidence,
                    "gate_6_value_ok":  value is not None,
                    "gate_7_object_ok": obj_ok,
                    "gate_7_reason":    obj_reason,
                    "gate_7_repair":    repair,
                    "gate_8_conf_ok":   conf_ok,
                    "gate_9_corrected": raw.get("_gate9_corrected", False),
                    "gate_10_enforced": raw.get("_gate10_enforced", False),
                    "final_trait":      final_trait,
                    "final_context":    final_context,
                }

                if value and obj_ok and conf_ok:
                    belief = ExtractedBelief(
                        trait=final_trait, value=value, context=final_context,
                        confidence=confidence, source=clause
                    )
                    clause_trace["beliefs"].append(belief_trace)
                    trace["beliefs"].append(belief)
                else:
                    belief_trace["blocked"] = True
                    clause_trace["beliefs"].append(belief_trace)
                    trace["blocked"].append({"clause": clause, "reason": "post_llm_gate",
                                              **belief_trace})

            trace["clauses"].append(clause_trace)

        # Sentence-scope Gate 10 pass (FM-163)
        before_sentence_pass = list(trace["beliefs"])
        trace["beliefs"] = gate_negation_enforcement_sentence(
            trace["beliefs"], sentence
        )

        # Log sentence-pass diffs for observability
        sentence_pass_flips = []
        for before, after in zip(before_sentence_pass, trace["beliefs"]):
            if before.value != after.value:
                sentence_pass_flips.append({
                    "trait": after.trait,
                    "context": after.context,
                    "from": before.value,
                    "to": after.value,
                })
        trace["sentence_pass"] = {
            "gate": "10_sentence",
            "name": "negation_sentence_scope",
            "flips": sentence_pass_flips,
        }

        return trace
