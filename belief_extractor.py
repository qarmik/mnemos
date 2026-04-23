"""
MNEMOS v0.22 — BeliefExtractor (L3 Ingestion Layer)

The pipeline Commander V specified:

  Sentence
    ↓
  Controlled clause splitting
    ↓
  For each clause:
    Gate 1 — Temporal
    Gate 2 — Uncertainty
    Gate 3 — Subject
    Gate 4 — Context normalization
    Gate 5 — LLM extraction
    Gate 6 — Value normalization
    Gate 7 — Object resolution check
    Gate 8 — Confidence filter
    ↓
  Write via upsert_belief()

Rules:
  - LLM extracts structure only. Never decides whether to write.
  - System decides truth. All write decisions are deterministic.
  - value ∈ {like, dislike} only. Neutral is never stored.
  - Absence of belief is more honest than a polluted belief.
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
    value:      str          # "like" or "dislike" only
    context:    str          # normalized, never empty (use "general")
    confidence: str          # "explicit" or "implicit"
    source:     str = ""     # original clause text


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


def normalize_context(raw_context: str) -> str:
    """Gate 4: normalize context string to canonical form."""
    if not raw_context or raw_context.lower() in ("general", "none", ""):
        return "general"

    c = raw_context.lower().strip()

    # Check explicit normalization map first
    for raw, norm in CONTEXT_NORMALIZATIONS.items():
        if raw in c:
            return norm

    # Fallback: lowercase, strip articles, collapse whitespace, replace spaces with _
    c = ARTICLE_PATTERN.sub("", c)
    c = WHITESPACE_PATTERN.sub("_", c.strip())
    return c or "general"


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


# ── Gate 7: Object resolution check ──────────────────────────────

AMBIGUOUS_OBJECTS = re.compile(
    r"^(it|them|this|that|those|these|one|ones)$", re.I
)


def gate_object_resolution(trait: str) -> bool:
    """Gate 7: block beliefs with unresolved object references.

    If trait contains an ambiguous pronoun, the object wasn't resolved.
    Returns True (passes) if object is resolved.
    """
    # trait should look like "coffee_preference", not "it_preference"
    obj = trait.replace("_preference", "").replace("_", " ").strip()
    if AMBIGUOUS_OBJECTS.match(obj):
        return False
    if len(obj) <= 1:
        return False
    return True


# ── Gate 8: Confidence filter ─────────────────────────────────────

def gate_confidence(confidence: str) -> bool:
    """Gate 8: only write explicit beliefs.

    "implicit" confidence = inferred, not stated. Do not write.
    """
    return confidence == "explicit"


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
        """Full pipeline: sentence → list of validated ExtractedBelief."""
        results = []

        # Step 1: Controlled clause splitting
        clauses = split_clauses(sentence)

        for clause in clauses:
            clause_beliefs = self._process_clause(clause)
            results.extend(clause_beliefs)

        return results

    def _process_clause(self, clause: str) -> List[ExtractedBelief]:
        """Run all 8 gates on a single clause."""

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

        results = []
        for raw in raw_beliefs:
            trait      = raw.get("trait", "").strip()
            raw_value  = raw.get("value", "").strip()
            raw_ctx    = raw.get("context", "general").strip()
            confidence = raw.get("confidence", "implicit").strip()

            # State transition override: if gate1 flagged state transition,
            # invert the value (stopped liking → dislike)
            if is_state_transition:
                if raw_value == "like":
                    raw_value = "dislike"
                elif raw_value == "dislike":
                    raw_value = "like"

            # Gate 4 — Context normalization
            context = normalize_context(raw_ctx)

            # Gate 6 — Value normalization
            value = normalize_value(raw_value)
            if value is None:
                continue  # neutral or unrecognizable — no write

            # Gate 7 — Object resolution
            if not gate_object_resolution(trait):
                continue

            # Gate 8 — Confidence filter
            if not gate_confidence(confidence):
                continue

            results.append(ExtractedBelief(
                trait=trait,
                value=value,
                context=context,
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

            for raw in raw_beliefs:
                trait      = raw.get("trait", "").strip()
                raw_value  = raw.get("value", "").strip()
                raw_ctx    = raw.get("context", "general").strip()
                confidence = raw.get("confidence", "implicit").strip()

                if is_state_transition:
                    if raw_value == "like":   raw_value = "dislike"
                    elif raw_value == "dislike": raw_value = "like"

                context = normalize_context(raw_ctx)   # Gate 4
                value   = normalize_value(raw_value)   # Gate 6
                obj_ok  = gate_object_resolution(trait)  # Gate 7
                conf_ok = gate_confidence(confidence)    # Gate 8

                belief_trace = {
                    "trait": trait, "raw_value": raw_value,
                    "value": value, "context": context,
                    "confidence": confidence,
                    "gate_6_value_ok":  value is not None,
                    "gate_7_object_ok": obj_ok,
                    "gate_8_conf_ok":   conf_ok,
                }

                if value and obj_ok and conf_ok:
                    belief = ExtractedBelief(
                        trait=trait, value=value, context=context,
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

        return trace
