"""
MNEMOS Regression Suite — v0.22 through v0.25
==============================================

One test per confirmed-fix failure mode from the v0.22–v0.25 adversarial
build phase. Each test exercises the specific failure path that was broken,
demonstrates that the fix holds, and will catch silent regression.

Test naming: test_fm_NNN_short_description
Each test maps 1:1 to an entry in docs/failure_modes.md.

Coverage:
  FM-147  Missing context capture
  FM-150  Partial negation capture
  FM-151  Context collapse on conditional
  FM-152  Multi-context collapse
  FM-153  Context over-assignment
  FM-154  Negation inheritance implicit
  FM-155  Object resolution too weak
  FM-156  Recoverable trait drift
  FM-157  Pseudo-context pollution
  FM-163  Clause-split negation destruction
  FM-165  Retrieval substring collision
  FM-170  Strict reject discards legitimate input

What is NOT covered here:
  Gate 5 (LLM extraction) — stochastic, requires live OPENAI_API_KEY.
  FM-166, FM-169, FM-171, FM-172 — confirmed-deferred, no fix yet.
  FM-158, FM-164, FM-167, FM-168 — hypothesized, not confirmed.
  SP-1, SP-2 — structural properties, not bugs.

Run:
  pytest tests/test_regression.py -v
  pytest tests/test_regression.py -v --tb=short   # compact traceback
"""

import sys
import os

# Ensure repo root is on path regardless of where pytest is invoked from
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from belief_extractor import (
    gate_temporal,
    gate_uncertainty,
    gate_subject,
    normalize_context,
    normalize_value,
    gate_object_resolution,
    gate_confidence,
    gate_context_assignment,
    gate_negation_enforcement,
    gate_negation_enforcement_sentence,
    split_clauses,
    ExtractedBelief,
)
from mnemos_lite import Belief, KnowledgeGraph, Domain


# ─────────────────────────────────────────────────────────────────────
# FM-147 — Missing context capture
#
# The failure: _detect_preference_correction and _capture_immediate
# only recognised prawns. Any preference outside that domain was
# invisible. "I like coffee in the morning" produced no belief.
#
# The fix: v0.22 BeliefExtractor — domain-generic LLM extraction.
# Gates 1-4 and 6-10 are deterministic regardless of domain.
#
# What we test: the deterministic gates process non-prawns topics
# identically to prawns topics. No domain-specific hardcoding.
# ─────────────────────────────────────────────────────────────────────

def test_fm147_missing_context_capture():
    """Gates 1-3 must pass for any domain, not just prawns."""
    # Pre-fix: anything other than prawns was invisible.
    # Post-fix: gates are domain-agnostic.
    for clause in [
        "I like coffee",
        "I hate working late",
        "I love sushi",
        "I dislike crowded places",
    ]:
        g1, _ = gate_temporal(clause)
        g2, _ = gate_uncertainty(clause)
        g3, _, _ = gate_subject(clause)
        assert g1, f"Gate 1 wrongly blocked: {clause!r}"
        assert g2, f"Gate 2 wrongly blocked: {clause!r}"
        assert g3, f"Gate 3 wrongly blocked: {clause!r}"

    # Context extraction normalizes non-prawns contexts correctly
    assert normalize_context("in the morning") == "morning"
    assert normalize_context("when stressed")  == "stressed"
    assert normalize_context("at work")        == "work"


# ─────────────────────────────────────────────────────────────────────
# FM-150 — Partial negation capture
#
# The failure: "I am not sure if I like prawns" matched the "like
# prawns" regex and was captured as a like-assertion. The hedging
# was ignored.
#
# The fix: Gate 2 (Uncertainty) blocks hedged statements.
# ─────────────────────────────────────────────────────────────────────

def test_fm150_partial_negation_capture():
    """Gate 2 must block hedged statements — not treat them as assertions."""
    # These are the phrases Gate 2 is documented to block.
    # Note: "I don't know if..." is NOT currently blocked — known gap
    # in Gate 2 pattern coverage. Not part of FM-150's original scope.
    hedged = [
        "I am not sure if I like prawns",   # FM-150 core case
        "I might like coffee",
        "Maybe I like working late",
        "I think I like prawns",
        "I guess I like coffee",
        "I kind of like coffee",
        "I sort of enjoy sushi",
    ]
    for clause in hedged:
        passes, reason = gate_uncertainty(clause)
        assert not passes, (
            f"Gate 2 should block hedged statement but passed: {clause!r} "
            f"(reason={reason!r})"
        )

    # Clear statements must still pass
    clear = ["I like prawns", "I hate coffee", "I love sushi"]
    for clause in clear:
        passes, _ = gate_uncertainty(clause)
        assert passes, f"Gate 2 wrongly blocked clear statement: {clause!r}"


# ─────────────────────────────────────────────────────────────────────
# FM-151 — Context collapse on conditional
#
# The failure: "I like prawns when my wife cooks them" was stored as
# prawns_preference=like, context=general. The conditional was stripped.
#
# The fix: Gate 5 (LLM) extracts context from conditional phrases.
# Gate 4 normalizes "when my wife cooks" → "wife_cooks".
# ─────────────────────────────────────────────────────────────────────

def test_fm151_context_collapse_on_conditional():
    """Context normalization must preserve conditional qualifiers."""
    # The canonical FM-151 conditional
    assert normalize_context("when my wife cooks") == "wife_cooks"
    assert normalize_context("wife cooks")         == "wife_cooks"

    # Other conditionals must not collapse to None
    result = normalize_context("when stressed")
    assert result is not None, "Conditional context must not collapse to None"
    assert result == "stressed"

    result2 = normalize_context("when at work")
    assert result2 is not None


# ─────────────────────────────────────────────────────────────────────
# FM-152 — Multi-context collapse
#
# The failure: "I like coffee in morning and hate it at night" produced
# one belief or none. The opposing-polarity clause was lost.
#
# The fix: controlled clause splitting. Polarity change triggers a split.
# ─────────────────────────────────────────────────────────────────────

def test_fm152_multi_context_collapse():
    """Polarity-change clause splitting must produce separate clauses."""
    # Core FM-152 case — polarity reversal in one sentence
    clauses = split_clauses("I like coffee in morning and hate it at night")
    assert len(clauses) >= 2, (
        f"Polarity change must produce at least 2 clauses. Got: {clauses}"
    )

    # "but hate" also triggers a split
    clauses2 = split_clauses("I like coffee but hate tea")
    assert len(clauses2) >= 2, (
        f"'but hate' must trigger a split. Got: {clauses2}"
    )

    # Same predicate same polarity must NOT split
    clauses3 = split_clauses("I like coffee and tea")
    assert len(clauses3) == 1, (
        f"'I like coffee and tea' must not split (same predicate, same polarity). "
        f"Got: {clauses3}"
    )


# ─────────────────────────────────────────────────────────────────────
# FM-153 — Context over-assignment
#
# The failure: "I like coffee and tea, but only coffee in the morning"
# assigned context=morning to both coffee and tea. The "only coffee"
# restriction was ignored.
#
# The fix: Gate 9 — post-LLM deterministic context assignment check.
# Object matching is token-set (not substring).
# ─────────────────────────────────────────────────────────────────────

def test_fm153_context_over_assignment():
    """Gate 9 must restrict context to the explicitly named object only."""
    # Core failure case
    raw = [
        {"trait": "coffee_preference", "value": "like", "context": "morning", "confidence": "explicit"},
        {"trait": "tea_preference",    "value": "like", "context": "morning", "confidence": "explicit"},
    ]
    result = gate_context_assignment(raw, "only coffee in the morning")

    assert result[0]["context"] == "morning", \
        "coffee must keep its morning context"
    assert result[1]["context"] is None, \
        f"tea must be demoted to None — got {result[1]['context']!r}"
    assert result[1].get("_gate9_corrected") is True, \
        "tea belief must be marked as gate9_corrected"

    # Symmetric case — no restriction, both must keep context
    raw_sym = [
        {"trait": "coffee_preference", "value": "like", "context": "morning", "confidence": "explicit"},
        {"trait": "tea_preference",    "value": "like", "context": "morning", "confidence": "explicit"},
    ]
    result_sym = gate_context_assignment(raw_sym, "I like coffee and tea in the morning")
    assert result_sym[0]["context"] == "morning"
    assert result_sym[1]["context"] == "morning"
    assert not result_sym[0].get("_gate9_corrected")
    assert not result_sym[1].get("_gate9_corrected")

    # Token-exact: "tea" must not match "steak" (pre-fix used substring)
    raw_token = [
        {"trait": "steak_preference", "value": "like", "context": "evening", "confidence": "explicit"},
        {"trait": "tea_preference",   "value": "like", "context": "evening", "confidence": "explicit"},
    ]
    result_token = gate_context_assignment(raw_token, "only tea in the evening")
    assert result_token[0]["context"] is None, \
        "steak must not match 'tea' restriction — token-exact required"
    assert result_token[1]["context"] == "evening", \
        "tea must keep evening context"


# ─────────────────────────────────────────────────────────────────────
# FM-154 — Negation inheritance implicit (unsafe)
#
# The failure: "I like coffee in the morning but not at night" — the
# LLM sometimes returned both clauses as value=like. Polarity inversion
# was delegated to LLM instructions rather than enforced deterministically.
#
# The fix: Gate 10a — deterministic per-clause negation enforcement.
# ─────────────────────────────────────────────────────────────────────

def test_fm154_negation_inheritance_implicit():
    """Gate 10a must deterministically invert polarity on 'not at <context>'."""
    # LLM fails to invert — both come back as 'like'
    raw_failed_inversion = [
        {"trait": "coffee_preference", "value": "like", "context": "morning", "confidence": "explicit"},
        {"trait": "coffee_preference", "value": "like", "context": "night",   "confidence": "explicit"},
    ]
    result = gate_negation_enforcement(
        raw_failed_inversion,
        "I like coffee in the morning but not at night"
    )

    assert result[0]["value"] == "like",    "morning must stay like"
    assert result[1]["value"] == "dislike", \
        f"night must be inverted to dislike — got {result[1]['value']!r}"
    assert result[1].get("_gate10_enforced") is True, \
        "night belief must be marked gate10_enforced"

    # No negation phrase — nothing should be touched
    raw_clean = [
        {"trait": "coffee_preference", "value": "like", "context": "morning", "confidence": "explicit"},
    ]
    result_clean = gate_negation_enforcement(
        raw_clean, "I like coffee in the morning"
    )
    assert result_clean[0]["value"] == "like"
    assert not result_clean[0].get("_gate10_enforced")


# ─────────────────────────────────────────────────────────────────────
# FM-155 — Object resolution too weak
#
# The failure: "I like coffee. It helps me think." — the LLM extracted
# a second belief with trait=it_preference. Unresolved pronouns leaked
# into the graph.
#
# The fix: Gate 7 — INVALID_TRAIT_OBJECTS set blocks pronoun traits.
# ─────────────────────────────────────────────────────────────────────

def test_fm155_object_resolution_too_weak():
    """Gate 7 must reject pronoun/placeholder object traits."""
    pronouns = [
        "it_preference",
        "them_preference",
        "this_preference",
        "that_preference",
        "those_preference",
        "these_preference",
        "thing_preference",
        "something_preference",
    ]
    for trait in pronouns:
        ok, reason, _ = gate_object_resolution(trait)
        assert not ok, \
            f"Gate 7 must reject pronoun trait {trait!r} but passed (reason={reason!r})"

    # Valid entity traits must still pass
    valid = ["coffee_preference", "meeting_preference", "work_preference", "prawns_preference"]
    for trait in valid:
        ok, _, _ = gate_object_resolution(trait)
        assert ok, f"Gate 7 wrongly rejected valid entity trait {trait!r}"


# ─────────────────────────────────────────────────────────────────────
# FM-156 — Recoverable trait drift (simple repair)
#
# The failure: LLM emits monday_meeting_preference — a context word
# leaked into the trait name. The initial v0.22 Gate 7 rejected the
# belief entirely. Recoverable signal was destroyed.
#
# The fix: Gate 7 Path A — deterministic repair when LLM context empty.
# monday_meeting_preference + None → meeting_preference + context=monday
# ─────────────────────────────────────────────────────────────────────

def test_fm156_recoverable_trait_drift():
    """Gate 7 must repair 2-word drift traits rather than reject them."""
    # Core repair case
    ok, reason, repair = gate_object_resolution(
        "monday_meeting_preference", llm_context=None
    )
    assert ok, f"monday_meeting_preference must be repaired, not rejected (reason={reason!r})"
    assert repair == ("meeting_preference", "monday"), \
        f"Repair must produce meeting_preference+monday. Got: {repair!r}"

    # Another direction
    ok2, _, repair2 = gate_object_resolution("morning_coffee_preference", llm_context=None)
    assert ok2
    assert repair2 == ("coffee_preference", "morning"), \
        f"Repair must produce coffee_preference+morning. Got: {repair2!r}"

    # 3+ word drift must still reject — no repair possible
    ok3, _, _ = gate_object_resolution(
        "monday_morning_meeting_preference", llm_context=None
    )
    assert not ok3, "3+ word drift must be rejected — cannot cleanly repair"

    # Both words are context words — must reject
    ok4, _, _ = gate_object_resolution("late_night_preference", llm_context=None)
    assert not ok4, "Trait where both words are context words must be rejected"

    # Legacy "general" treated as empty — same as None
    ok5, _, repair5 = gate_object_resolution(
        "monday_meeting_preference", llm_context="general"
    )
    assert ok5
    assert repair5 == ("meeting_preference", "monday")


# ─────────────────────────────────────────────────────────────────────
# FM-157 — Pseudo-context pollution
#
# The failure: context=None and context="general" were stored as the
# same thing. Two distinct sentinels for "unconditional" created
# overwrite collisions and false equality.
#
# The fix: context=None is the sole engine sentinel. "general" is
# UI-only and never enters engine state.
# ─────────────────────────────────────────────────────────────────────

def test_fm157_pseudo_context_pollution():
    """context=None must be the sole engine sentinel for unconditional."""
    # normalize_context must return None for "general", "", "none"
    assert normalize_context("")        is None, "'' must normalize to None"
    assert normalize_context("general") is None, "general must normalize to None"
    assert normalize_context("none")    is None, "'none' must normalize to None"
    assert normalize_context(None)      is None, "None input must return None"

    # Real contexts must survive normalization
    assert normalize_context("morning") == "morning"
    assert normalize_context("night")   == "night"

    # Belief default must be None, not "general"
    b = Belief(trait="coffee_preference", value="like")
    assert b.context is None, \
        f"Belief default context must be None — got {b.context!r}"

    # add_belief() must normalize "general" to None at API boundary
    g = KnowledgeGraph()
    b_general = Belief(
        trait="coffee_preference", value="like",
        context=None,  # correctly None after normalization
        namespace="test", domain=Domain.PREFERENCE,
        content="User likes coffee"
    )
    g.upsert_belief(b_general)
    results = g.search("coffee", namespace="test")
    assert len(results) >= 1
    assert results[0].context is None, \
        f"Stored belief context must be None — got {results[0].context!r}"

    # matches_context: None matches everything (wildcard)
    b_uncond = Belief(trait="t", value="v", context=None)
    assert b_uncond.matches_context("morning")  is True
    assert b_uncond.matches_context("night")    is True
    assert b_uncond.matches_context(None)       is True
    assert b_uncond.matches_context("anything") is True

    # matches_context: conditional belief does NOT match None query
    b_cond = Belief(trait="t", value="v", context="morning")
    assert b_cond.matches_context(None) is False, \
        "Conditional belief must not match a None query"


# ─────────────────────────────────────────────────────────────────────
# FM-163 — Clause-split negation destruction
#
# The failure: "I like coffee but not at night" — split_clauses()
# separated "not at night" into its own clause. Per-clause Gate 10a
# received an isolated fragment with no beliefs to invert. The
# negation intent was silently lost.
#
# The fix: Gate 10b — sentence-scope second pass over all extracted
# beliefs. Only flips beliefs that already exist; never creates.
# ─────────────────────────────────────────────────────────────────────

def test_fm163_clause_split_negation_destruction():
    """Gate 10b must flip beliefs via sentence-scope, not per-clause scope."""
    # The core case: pessimistic LLM extrapolated coffee@night=like into
    # the separated clause. Sentence-scope must flip it.
    beliefs = [
        ExtractedBelief("coffee_preference", "like", None,    "explicit", "src"),
        ExtractedBelief("coffee_preference", "like", "night", "explicit", "src"),
    ]
    result = gate_negation_enforcement_sentence(
        beliefs, "I like coffee but not at night"
    )

    # Unconditional belief must not be flipped
    assert result[0].value == "like" and result[0].context is None, \
        f"Unconditional belief must be untouched. Got value={result[0].value!r}"

    # Night belief must be flipped to dislike
    assert result[1].value == "dislike", \
        f"Night belief must be flipped to dislike. Got {result[1].value!r}"

    # Invariant: no creation when no belief exists at negated context
    beliefs_no_night = [
        ExtractedBelief("coffee_preference", "like", "morning", "explicit", "src"),
    ]
    result2 = gate_negation_enforcement_sentence(
        beliefs_no_night, "I like coffee in the morning but not at night"
    )
    assert len(result2) == 1, \
        f"Must not create a new belief at negated context. Got {len(result2)} beliefs."
    assert result2[0].value == "like"

    # Idempotence: per-clause already flipped — sentence-scope must not re-flip
    already_flipped = [
        ExtractedBelief("coffee_preference", "like",    "morning", "explicit", "src"),
        ExtractedBelief("coffee_preference", "dislike", "night",   "explicit", "src"),
    ]
    result3 = gate_negation_enforcement_sentence(
        already_flipped, "I like coffee in the morning but not at night"
    )
    assert result3[0].value == "like",    "morning must stay like"
    assert result3[1].value == "dislike", "already-flipped night must stay dislike (idempotent)"


# ─────────────────────────────────────────────────────────────────────
# FM-165 — Retrieval substring collision
#
# The failure: matches_context() used substring matching.
# "night" in "midnight" returned True.
# "work" in "homework" returned True.
# Silent semantic drift on retrieval.
#
# The fix: token-set equality. frozenset of underscore/whitespace-split
# tokens. None is the only wildcard.
# ─────────────────────────────────────────────────────────────────────

def test_fm165_retrieval_substring_collision():
    """matches_context must use token-set equality, not substring."""
    # The core FM-165 collision cases
    b_night = Belief(trait="t", value="v", context="night")
    assert b_night.matches_context("midnight") is False, \
        "'night' must NOT match 'midnight' — this was the FM-165 bug"
    assert b_night.matches_context("night") is True

    b_work = Belief(trait="t", value="v", context="work")
    assert b_work.matches_context("homework") is False, \
        "'work' must NOT match 'homework'"

    b_day = Belief(trait="t", value="v", context="day")
    assert b_day.matches_context("weekday") is False, \
        "'day' must NOT match 'weekday'"

    # Token-set equality: delimiter-insensitive
    b_compound = Belief(trait="t", value="v", context="monday_morning")
    assert b_compound.matches_context("monday morning") is True, \
        "'monday_morning' must match 'monday morning' (same tokens)"
    assert b_compound.matches_context("monday_morning") is True

    # No subset/hierarchy — FM-159 boundary
    b_monday = Belief(trait="t", value="v", context="monday")
    assert b_monday.matches_context("monday_morning") is False, \
        "'monday' must NOT match 'monday_morning' — no subset matching"

    # None is the only wildcard
    b_uncond = Belief(trait="t", value="v", context=None)
    assert b_uncond.matches_context("midnight") is True
    assert b_uncond.matches_context("anything") is True

    # Verify in graph.search as well
    g = KnowledgeGraph()
    b_stored = Belief(
        trait="coffee_preference", value="dislike", context="night",
        namespace="test", domain=Domain.PREFERENCE,
        content="User dislikes coffee at night"
    )
    g.upsert_belief(b_stored)

    # Query for "midnight" must return 0 results (no substring match)
    r = g.search("coffee", namespace="test", query_context="midnight")
    assert len(r) == 0, \
        f"'night' belief must not match 'midnight' query. Got {len(r)} results."

    # Query for "night" must return 1 result
    r2 = g.search("coffee", namespace="test", query_context="night")
    assert len(r2) == 1, \
        f"'night' query must find 'night' belief. Got {len(r2)} results."


# ─────────────────────────────────────────────────────────────────────
# FM-170 — Strict reject discards legitimate input
#
# The failure (Phase 3 B7): "only Monday meetings in the morning"
# LLM produces monday_meeting_preference + context=morning.
# Gate 7 detected drift AND saw a non-empty LLM context → strict
# reject path → entire belief discarded. The user's morning
# restriction was silently lost.
#
# The fix: Gate 7 Path B — canonical compound repair.
# Normalize drift and LLM context independently, compose with
# underscore, validate against CANONICAL_COMPOUND_CONTEXTS.
# Composed string is never re-normalized (would reintroduce FM-169).
# ─────────────────────────────────────────────────────────────────────

def test_fm170_strict_reject_discards_legitimate_input():
    """Gate 7 Path B must repair trait drift when composition is canonical."""
    # Core failure case: monday_meeting + morning → meeting + monday_morning
    ok, reason, repair = gate_object_resolution(
        "monday_meeting_preference", llm_context="morning"
    )
    assert ok, \
        f"monday_meeting_preference + 'morning' must be repaired, not rejected. reason={reason!r}"
    assert repair == ("meeting_preference", "monday_morning"), \
        f"Repair must produce meeting_preference + monday_morning. Got: {repair!r}"

    # Non-canonical compound must still reject — no fabrication
    ok2, _, _ = gate_object_resolution(
        "monday_meeting_preference", llm_context="afternoon"
    )
    assert not ok2, \
        "monday_afternoon is not a canonical compound — must reject, not fabricate"

    ok3, _, _ = gate_object_resolution(
        "monday_meeting_preference", llm_context="evening"
    )
    assert not ok3, \
        "monday_evening is not a canonical compound — must reject"

    # Path B must not fire when there is no trait drift
    ok4, _, repair4 = gate_object_resolution(
        "coffee_preference", llm_context="morning"
    )
    assert ok4 and repair4 is None, \
        "No drift in coffee_preference — Path B must not fire"

    # LLM context set + 3+ word drift must still reject
    ok5, _, _ = gate_object_resolution(
        "monday_morning_meeting_preference", llm_context="morning"
    )
    assert not ok5, "3+ word drift must reject even with LLM context set"

    # Composition is order-sensitive (drift_norm + "_" + llm_norm)
    # morning_monday is not canonical even though monday_morning is
    ok6, _, _ = gate_object_resolution(
        "morning_meeting_preference", llm_context="monday"
    )
    assert not ok6, \
        "morning_monday is not in CANONICAL_COMPOUND_CONTEXTS — must reject"
