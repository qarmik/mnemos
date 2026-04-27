"""
MNEMOS Verification Script
==========================

Verifies the deterministic core of the BeliefExtractor pipeline.

WHAT THIS VERIFIES:
  - Gate 1  (Temporal guard)
  - Gate 2  (Uncertainty guard)
  - Gate 3  (Subject guard)
  - Gate 4  (Context normalization)
  - Gate 6  (Value normalization)
  - Gate 7  (Object/trait validation + repair — FM-155, FM-156, FM-170)
  - Gate 8  (Confidence filter)
  - Gate 9  (Context assignment validation — FM-153)
  - Gate 10a (Per-clause negation enforcement — FM-154)
  - Gate 10b (Sentence-scope negation second pass — FM-163)
  - FM-157  (context=None engine invariant)
  - FM-165  (token-set retrieval equality)
  - FM-169  (normalization map key ordering — deferred, currently failing)

WHAT THIS DOES NOT VERIFY:
  - Gate 5 (LLM extraction) — stochastic by design. Output depends on
    gpt-5.4-mini and the OPENAI_API_KEY. Cannot be deterministically
    verified without a live API call.
  - SP-1 (LLM coverage boundary) — structural property, not a bug.
    The system is "deterministic over a stochastic source." If the LLM
    does not extract a belief, no gate can repair it.
  - SP-2 (pessimistic-LLM hypothesis) — unvalidated until live API
    adversarial sequences are run.
  - Session behavior, cross-session memory, UAI tracking — require a
    live session runner.

USAGE:
  python verify.py           # run all checks, print pass/fail
  python verify.py --verbose # show detail on each check
  python verify.py --fast    # skip slow checks (currently all are fast)

EXIT CODES:
  0  — all checks passed
  1  — one or more checks failed
"""

import sys
import argparse
from dataclasses import dataclass
from typing import List, Optional


# ── Result tracking ───────────────────────────────────────────────────

@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    fm: str = ""


results: List[CheckResult] = []


def check(name: str, condition: bool, detail: str = "", fm: str = "") -> bool:
    result = CheckResult(name=name, passed=condition, detail=detail, fm=fm)
    results.append(result)
    return condition


# ── Import the modules under test ─────────────────────────────────────

try:
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
        ExtractedBelief,
        CANONICAL_COMPOUND_CONTEXTS,
    )
    from mnemos_lite import Belief, KnowledgeGraph, Domain
    IMPORT_OK = True
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
    print("Ensure you are running from the repo root: python verify.py")
    sys.exit(1)


# ── Gate 1: Temporal guard ────────────────────────────────────────────

def verify_gate1():
    cases = [
        ("I used to like prawns",      False, "used_to_blocked"),
        ("I previously hated coffee",  False, "previously_blocked"),
        ("I hate prawns",              True,  "present_tense_passes"),
        ("I stopped liking prawns",    True,  "state_transition_passes"),
        ("I used to hate it but now I love it", True, "but_now_override"),
    ]
    for text, expected_pass, label in cases:
        passes, _ = gate_temporal(text)
        check(f"gate1/{label}", passes == expected_pass,
              fm="FM-152/Gate1",
              detail=f"'{text}' -> passes={passes}, expected={expected_pass}")


# ── Gate 2: Uncertainty guard ─────────────────────────────────────────

def verify_gate2():
    cases = [
        ("I might like prawns",             False, "might_blocked"),
        ("I am not sure if I like prawns",  False, "not_sure_blocked"),
        ("I like prawns",                   True,  "clear_statement_passes"),
        ("I hate prawns",                   True,  "clear_dislike_passes"),
    ]
    for text, expected_pass, label in cases:
        passes, _ = gate_uncertainty(text)
        check(f"gate2/{label}", passes == expected_pass,
              fm="FM-150/Gate2",
              detail=f"'{text}' -> passes={passes}, expected={expected_pass}")


# ── Gate 3: Subject guard ─────────────────────────────────────────────

def verify_gate3():
    cases = [
        ("I like coffee",                True,  "first_person_passes"),
        ("My wife likes coffee",         False, "third_party_blocked"),
        ("My wife and I like coffee",    True,  "explicit_i_passes"),
        ("We like coffee",               False, "we_blocked"),
    ]
    for text, expected_pass, label in cases:
        passes, _, _ = gate_subject(text)
        check(f"gate3/{label}", passes == expected_pass,
              fm="FM-153/Gate3",
              detail=f"'{text}' -> passes={passes}, expected={expected_pass}")


# ── Gate 4: Context normalization / FM-157 ────────────────────────────

def verify_gate4_and_fm157():
    # FM-157: None is the sole engine sentinel for unconditional
    cases = [
        ("",          None,          "empty_returns_none"),
        ("general",   None,          "general_returns_none"),
        ("none",      None,          "none_string_returns_none"),
        ("morning",   "morning",     "morning_preserved"),
        ("in the morning", "morning", "in_the_morning_normalized"),
        ("at night",  "night",       "at_night_normalized"),
        ("when stressed", "stressed", "stressed_normalized"),
    ]
    for raw, expected, label in cases:
        result = normalize_context(raw)
        check(f"gate4_fm157/{label}", result == expected,
              fm="FM-157/Gate4",
              detail=f"normalize_context({raw!r}) = {result!r}, expected {expected!r}")

    # Also verify Belief default
    b = Belief(trait="t", value="v")
    check("fm157/belief_default_none", b.context is None,
          fm="FM-157",
          detail=f"Belief default context = {b.context!r}, expected None")


# ── Gate 6: Value normalization ───────────────────────────────────────

def verify_gate6():
    cases = [
        ("like",    "like",    "like_normalized"),
        ("love",    "like",    "love_to_like"),
        ("enjoy",   "like",    "enjoy_to_like"),
        ("dislike", "dislike", "dislike_normalized"),
        ("hate",    "dislike", "hate_to_dislike"),
        ("neutral", None,      "neutral_blocked"),
        ("okay",    None,      "okay_blocked"),
        ("fine",    None,      "fine_blocked"),
    ]
    for raw, expected, label in cases:
        result = normalize_value(raw)
        check(f"gate6/{label}", result == expected,
              fm="Gate6",
              detail=f"normalize_value({raw!r}) = {result!r}, expected {expected!r}")


# ── Gate 7: Object/trait validation — FM-155, FM-156, FM-170 ─────────

def verify_gate7():
    # FM-155: pronoun rejection
    pronoun_cases = [
        ("it_preference",   False, "it_rejected"),
        ("them_preference", False, "them_rejected"),
        ("this_preference", False, "this_rejected"),
    ]
    for trait, expected_ok, label in pronoun_cases:
        ok, _, _ = gate_object_resolution(trait)
        check(f"gate7_fm155/{label}", ok == expected_ok,
              fm="FM-155",
              detail=f"gate_object_resolution({trait!r}) -> ok={ok}, expected {expected_ok}")

    # FM-156: simple repair (LLM context empty)
    repair_cases = [
        ("monday_meeting_preference",  None,    True,  ("meeting_preference", "monday"),  "monday_meeting_repaired"),
        ("morning_coffee_preference",  None,    True,  ("coffee_preference", "morning"),  "morning_coffee_repaired"),
        ("monday_morning_meeting_preference", None, False, None,                          "three_word_rejected"),
        ("late_night_preference",      None,    False, None,                              "both_context_words_rejected"),
    ]
    for trait, llm_ctx, expected_ok, expected_repair, label in repair_cases:
        ok, _, repair = gate_object_resolution(trait, llm_context=llm_ctx)
        check(f"gate7_fm156/{label}_ok", ok == expected_ok,
              fm="FM-156",
              detail=f"gate_object_resolution({trait!r}) -> ok={ok}, expected {expected_ok}")
        if expected_repair is not None:
            check(f"gate7_fm156/{label}_repair", repair == expected_repair,
                  fm="FM-156",
                  detail=f"repair={repair!r}, expected {expected_repair!r}")

    # FM-170: canonical compound repair (LLM context set)
    ok, _, repair = gate_object_resolution("monday_meeting_preference", llm_context="morning")
    check("gate7_fm170/canonical_compound_repair",
          ok and repair == ("meeting_preference", "monday_morning"),
          fm="FM-170",
          detail=f"monday_meeting + morning -> ok={ok}, repair={repair!r}")

    ok, _, _ = gate_object_resolution("monday_meeting_preference", llm_context="afternoon")
    check("gate7_fm170/non_canonical_rejected", not ok,
          fm="FM-170",
          detail="monday_meeting + afternoon should reject (monday_afternoon not canonical)")

    # Single-word valid entities must pass through unchanged
    for trait in ["coffee_preference", "meeting_preference", "work_preference"]:
        ok, _, repair = gate_object_resolution(trait)
        check(f"gate7/valid_entity_{trait.replace('_preference','')}", ok and repair is None,
              fm="FM-156",
              detail=f"{trait} should pass with no repair, got ok={ok} repair={repair!r}")


# ── Gate 8: Confidence filter ─────────────────────────────────────────

def verify_gate8():
    check("gate8/explicit_passes", gate_confidence("explicit") is True, fm="Gate8")
    check("gate8/implicit_blocked", gate_confidence("implicit") is False, fm="Gate8")


# ── Gate 9: Context assignment validation — FM-153 ───────────────────

def verify_gate9():
    # Over-assignment case: "only coffee in the morning" — tea must be demoted
    raw = [
        {"trait": "coffee_preference", "value": "like", "context": "morning", "confidence": "explicit"},
        {"trait": "tea_preference",    "value": "like", "context": "morning", "confidence": "explicit"},
    ]
    result = gate_context_assignment(raw, "only coffee in the morning")
    check("gate9_fm153/coffee_keeps_morning",
          result[0]["context"] == "morning",
          fm="FM-153", detail=f"coffee context={result[0]['context']!r}")
    check("gate9_fm153/tea_demoted_to_none",
          result[1]["context"] is None,
          fm="FM-153", detail=f"tea context={result[1]['context']!r}, expected None")

    # Symmetric case: "coffee and tea in the morning" — both should keep morning
    raw_sym = [
        {"trait": "coffee_preference", "value": "like", "context": "morning", "confidence": "explicit"},
        {"trait": "tea_preference",    "value": "like", "context": "morning", "confidence": "explicit"},
    ]
    result_sym = gate_context_assignment(raw_sym, "I like coffee and tea in the morning")
    check("gate9/symmetric_untouched_coffee",
          result_sym[0]["context"] == "morning",
          fm="FM-153", detail="Symmetric case: coffee must keep morning")
    check("gate9/symmetric_untouched_tea",
          result_sym[1]["context"] == "morning",
          fm="FM-153", detail="Symmetric case: tea must keep morning")

    # Token-exact matching: "tea" must not match "steak"
    raw_token = [
        {"trait": "steak_preference", "value": "like", "context": "evening", "confidence": "explicit"},
        {"trait": "tea_preference",   "value": "like", "context": "evening", "confidence": "explicit"},
    ]
    result_token = gate_context_assignment(raw_token, "only tea in the evening")
    check("gate9/token_exact_steak_not_tea",
          result_token[0]["context"] is None,
          fm="FM-153", detail=f"steak context={result_token[0]['context']!r}, should be None (not tea)")
    check("gate9/token_exact_tea_keeps_evening",
          result_token[1]["context"] == "evening",
          fm="FM-153", detail="tea should keep evening context")


# ── Gate 10a: Per-clause negation — FM-154 ────────────────────────────

def verify_gate10a():
    raw = [
        {"trait": "coffee_preference", "value": "like", "context": "morning", "confidence": "explicit"},
        {"trait": "coffee_preference", "value": "like", "context": "night",   "confidence": "explicit"},
    ]
    result = gate_negation_enforcement(raw, "I like coffee in the morning but not at night")
    check("gate10a_fm154/morning_stays_like",
          result[0]["value"] == "like",
          fm="FM-154", detail=f"morning value={result[0]['value']!r}")
    check("gate10a_fm154/night_flipped_to_dislike",
          result[1]["value"] == "dislike",
          fm="FM-154", detail=f"night value={result[1]['value']!r}")

    # No negation phrase — nothing should change
    raw_clean = [
        {"trait": "coffee_preference", "value": "like", "context": "morning", "confidence": "explicit"},
    ]
    result_clean = gate_negation_enforcement(raw_clean, "I like coffee in the morning")
    check("gate10a/no_negation_untouched",
          result_clean[0]["value"] == "like",
          fm="FM-154", detail="No 'not at' phrase — should be untouched")


# ── Gate 10b: Sentence-scope negation — FM-163 ───────────────────────

def verify_gate10b():
    # Core case: cross-clause negation that per-clause Gate 10a would miss
    beliefs = [
        ExtractedBelief("coffee_preference", "like", None,    "explicit", "x"),
        ExtractedBelief("coffee_preference", "like", "night", "explicit", "x"),
    ]
    result = gate_negation_enforcement_sentence(beliefs, "I like coffee but not at night")
    check("gate10b_fm163/general_belief_untouched",
          result[0].value == "like" and result[0].context is None,
          fm="FM-163", detail=f"unconditional belief: value={result[0].value!r}, ctx={result[0].context!r}")
    check("gate10b_fm163/night_flipped_to_dislike",
          result[1].value == "dislike",
          fm="FM-163", detail=f"night belief: value={result[1].value!r}")

    # Idempotence: per-clause already flipped — sentence-scope must not re-flip
    beliefs_already_flipped = [
        ExtractedBelief("coffee_preference", "like",    "morning", "explicit", "x"),
        ExtractedBelief("coffee_preference", "dislike", "night",   "explicit", "x"),
    ]
    result2 = gate_negation_enforcement_sentence(
        beliefs_already_flipped, "I like coffee in the morning but not at night"
    )
    check("gate10b_fm163/idempotent_no_double_flip",
          result2[0].value == "like" and result2[1].value == "dislike",
          fm="FM-163", detail="Per-clause already flipped — sentence-scope must not re-flip")

    # Invariant: no creation when no existing belief at negated context
    beliefs_no_night = [
        ExtractedBelief("coffee_preference", "like", "morning", "explicit", "x"),
    ]
    result3 = gate_negation_enforcement_sentence(
        beliefs_no_night, "I like coffee in the morning but not at night"
    )
    check("gate10b_fm163/no_creation",
          len(result3) == 1 and result3[0].value == "like",
          fm="FM-163",
          detail=f"No night belief exists — must not create one. Got {len(result3)} beliefs.")


# ── FM-165: Token-set retrieval equality ─────────────────────────────

def verify_fm165():
    cases = [
        (None,             "anything",       True,  "none_is_wildcard"),
        (None,             None,             True,  "none_matches_none"),
        ("night",          "night",          True,  "exact_match"),
        ("night",          "midnight",       False, "night_not_midnight"),     # core FM-165 case
        ("midnight",       "night",          False, "midnight_not_night"),
        ("work",           "homework",       False, "work_not_homework"),      # substring trap
        ("day",            "weekday",        False, "day_not_weekday"),
        ("monday_morning", "monday_morning", True,  "compound_exact"),
        ("monday morning", "monday_morning", True,  "delimiter_insensitive"),  # spaces == underscores
        ("monday",         "monday_morning", False, "no_subset_match"),        # FM-159 boundary
        ("night",          None,             False, "conditional_plus_none_query"),
    ]
    for belief_ctx, query, expected, label in cases:
        b = Belief(trait="t", value="v", context=belief_ctx)
        got = b.matches_context(query)
        check(f"fm165/{label}", got == expected,
              fm="FM-165",
              detail=f"Belief(ctx={belief_ctx!r}).matches_context({query!r}) = {got}, expected {expected}")


# ── FM-169: Normalization shadowing (known failure — deferred) ────────

def verify_fm169_status():
    """
    FM-169 is confirmed-and-deferred. The normalization map uses substring
    iteration, so shorter keys shadow longer ones.

    'monday mornings' should normalize to 'monday_morning' but currently
    returns 'morning' because the 'mornings -> morning' key matches first.

    This check documents the known failure — it passes when the bug is
    present and fails when FM-169 is fixed. This is intentional.
    """
    result = normalize_context("monday mornings")
    # Current (buggy) behavior: returns 'morning'
    # Fixed behavior: should return 'monday_morning'
    is_shadowed = (result == "morning")
    check("fm169/normalization_shadowing_present",
          is_shadowed,
          fm="FM-169 (KNOWN DEFERRED BUG)",
          detail=(
              f"normalize_context('monday mornings') = {result!r}. "
              f"Currently returns 'morning' due to substring shadowing. "
              f"Expected 'monday_morning' after fix. "
              f"This check PASSES when the bug is present and FAILS when FM-169 is fixed."
          ))


# ── Graph invariants ──────────────────────────────────────────────────

def verify_graph_invariants():
    """
    Verify core graph invariants that the code structurally enforces.
    These map to architecture axioms and FM fixes.
    """
    g = KnowledgeGraph()

    # Invariant 1: one belief per (trait, namespace, context) — FM-121 / upsert_belief
    b1 = Belief(trait="coffee_preference", value="like",    context="morning",
                namespace="test", domain=Domain.PREFERENCE,
                content="User likes coffee in the morning")
    b2 = Belief(trait="coffee_preference", value="dislike", context="morning",
                namespace="test", domain=Domain.PREFERENCE,
                content="User dislikes coffee in the morning")
    g.upsert_belief(b1)
    g.upsert_belief(b2)  # must update in place, not duplicate
    results_q = g.search("coffee", namespace="test", query_context="morning")
    check("graph_invariant/one_belief_per_triple",
          len(results_q) == 1,
          fm="FM-121",
          detail=f"upsert_belief must produce 1 belief per (trait, ns, ctx). Got {len(results_q)}.")
    if results_q:
        check("graph_invariant/latest_wins",
              results_q[0].value == "dislike",
              fm="FM-121",
              detail=f"Last write wins. Expected dislike, got {results_q[0].value!r}.")

    # Invariant 2: context=None belief matches any query (FM-157 / None-wildcard)
    g2 = KnowledgeGraph()
    b_uncond = Belief(trait="tea_preference", value="like", context=None,
                      namespace="test2", domain=Domain.PREFERENCE,
                      content="User likes tea")
    g2.add_belief(b_uncond)
    r_morning = g2.search("tea", namespace="test2", query_context="morning")
    check("graph_invariant/none_context_is_wildcard",
          len(r_morning) >= 1,
          fm="FM-157",
          detail=f"context=None belief must match any query_context. Got {len(r_morning)} results.")

    # Invariant 3: conditional belief does NOT match a different context (FM-165)
    g3 = KnowledgeGraph()
    b_night = Belief(trait="coffee_preference", value="dislike", context="night",
                     namespace="test3", domain=Domain.PREFERENCE,
                     content="User dislikes coffee at night")
    g3.add_belief(b_night)
    r_midnight = g3.search("coffee", namespace="test3", query_context="midnight")
    check("graph_invariant/night_not_midnight",
          len(r_midnight) == 0,
          fm="FM-165",
          detail=f"'night' belief must not match 'midnight' query. Got {len(r_midnight)} results.")


# ── Runner ────────────────────────────────────────────────────────────

def run_all(verbose: bool = False) -> bool:
    suites = [
        ("Gate 1: Temporal",                 verify_gate1),
        ("Gate 2: Uncertainty",              verify_gate2),
        ("Gate 3: Subject",                  verify_gate3),
        ("Gate 4 + FM-157: Context / None",  verify_gate4_and_fm157),
        ("Gate 6: Value normalization",      verify_gate6),
        ("Gate 7: FM-155/156/170",           verify_gate7),
        ("Gate 8: Confidence filter",        verify_gate8),
        ("Gate 9: FM-153 Context assign",    verify_gate9),
        ("Gate 10a: FM-154 Per-clause neg",  verify_gate10a),
        ("Gate 10b: FM-163 Sentence neg",    verify_gate10b),
        ("FM-165: Token-set retrieval",      verify_fm165),
        ("FM-169: Shadowing (deferred)",     verify_fm169_status),
        ("Graph invariants",                 verify_graph_invariants),
    ]

    suite_results = {}
    for suite_name, fn in suites:
        before = len(results)
        fn()
        suite_checks = results[before:]
        passed = sum(1 for r in suite_checks if r.passed)
        total  = len(suite_checks)
        suite_results[suite_name] = (passed, total, suite_checks)

    # ── Summary ───────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("MNEMOS VERIFICATION RESULTS")
    print("=" * 70)
    print()

    total_passed = 0
    total_checks = 0
    any_unexpected_failure = False

    for suite_name, (passed, total, checks) in suite_results.items():
        status = "✓" if passed == total else "✗"
        print(f"  {status}  {suite_name}  ({passed}/{total})")
        total_passed += passed
        total_checks += total

        if verbose or passed < total:
            for r in checks:
                icon = "    ✓" if r.passed else "    ✗"
                fm_tag = f" [{r.fm}]" if r.fm else ""
                print(f"{icon} {r.name}{fm_tag}")
                if not r.passed and r.detail:
                    print(f"       {r.detail}")

        # FM-169 check is expected to pass (documents a known deferred bug)
        # Any other failure is unexpected
        for r in checks:
            if not r.passed and "FM-169" not in r.fm:
                any_unexpected_failure = True

    print()
    print("=" * 70)
    print(f"  Total: {total_passed}/{total_checks} checks passed")
    print()
    print("  Deterministic core:  VERIFIED" if not any_unexpected_failure
          else "  Deterministic core:  FAILURES PRESENT")
    print("  Stochastic boundary: Gate 5 (LLM extraction) not covered — by design")
    print("  SP-1 acknowledged:   system is 'deterministic over stochastic source'")
    print("  SP-2 unvalidated:    live API run required for FM-163 full validation")
    print("=" * 70)
    print()

    return not any_unexpected_failure


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify the MNEMOS deterministic gate pipeline."
    )
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detail on every check, not just failures.")
    parser.add_argument("--fast", action="store_true",
                        help="Reserved for future use (all checks are currently fast).")
    args = parser.parse_args()

    ok = run_all(verbose=args.verbose)
    sys.exit(0 if ok else 1)
