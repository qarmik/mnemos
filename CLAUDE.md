# MNEMOS — Project Context for Claude Code / Cowork

## What this repo is

MNEMOS is a structured AI memory architecture — 17 layers, 9 axioms,
172 failure modes catalogued (FM-01 through FM-172, with permanent
numbering gaps at FM-122–146 and FM-158–162).

Current working artifacts:
- `mnemos_lite.py` — core orchestrator (~2860 lines, v0.25)
- `belief_extractor.py` — L3 ingestion layer, 10-gate pipeline (~1130 lines, v0.25)
- `mnemos_session.py` — real session runner (OpenAI API)

Read `README.md` before any non-trivial change. Read
`docs/architecture.md` before touching the gate pipeline or
`BeliefExtractor`. Read `docs/failure_modes.md` before naming
a new failure mode — check the register first.

## Runtime — critical

**Model: gpt-5.4-mini (OpenAI — NOT Anthropic)**
**API: OPENAI_API_KEY environment variable**
**Only required runtime dependency: openai>=2.31.0**

## Workflow (non-negotiable — preserve it)

1. Qarmik proposes an idea or change, usually from his phone via Dispatch.
2. Claude drafts the implementation approach AND the diff.
3. Qarmik takes that to ChatGPT (Commander V) for adversarial critique.
4. Qarmik relays Commander V's critique back. Claude either pushes back
   (with concrete evidence) on invalid critiques or implements valid ones.
5. Iterate until convergence.
6. Only then: commit and push.

**Do NOT commit on the first draft.** Always produce the diff and wait
for Qarmik to return with Commander V's review. The adversarial loop is
the project's quality mechanism — skipping it defeats the methodology.

Never force-push. Never push to `main` without explicit "push to main"
instruction in that session.

## Hard rules

- For exploratory or risky changes: branch named `fm-XXX-shortdesc`
  or `feat/shortdesc`.
- Always show the unified diff and a one-paragraph rationale before
  any commit.
- Commit messages: imperative mood, prefix with `feat:`, `fix:`,
  `fm-XXX:`, `docs:`, `refactor:`, or `test:`. Reference FM number
  when applicable.
- Do not delete or rewrite anything in `docs/failure_modes.md` —
  only append. New FM entries require: name, trigger, system behavior,
  why it fails, fix direction, status.
- The `.claude/` local session folder must not be committed.

## Coding conventions

- Python 3.8+ floor (repo runs on 3.14 — do not use 3.14-only syntax).
- Match existing style: dataclasses, Beta(α,β) for confidence, explicit
  Domain enum usage.
- New beliefs/layers must respect the 9 Axioms (see README). If a
  change appears to violate one, stop and flag it.
- New failure modes: check `docs/failure_modes.md` for next available
  number. Current highest assigned: FM-172. Next: FM-173.
- The `context` field on `Belief` is `Optional[str]`. `None` means
  unconditional. The string `"general"` must never enter engine state —
  it is UI-only. This is FM-157 and is non-negotiable.

## Gate pipeline invariants (belief_extractor.py)

If you touch `belief_extractor.py`, these must hold after your change:

- LLM extracts structure only. System decides truth. Gate 5 is the
  only point where the LLM acts.
- Gate 7 returns a **3-tuple**: `(passes, reason, repair)`. A 2-tuple
  anywhere is a regression from v0.23.
- Gate 9 and Gate 10 receive the original clause string directly
  alongside raw beliefs — never reconstructed.
- `gate_negation_enforcement_sentence()` only flips beliefs that
  already exist. Never creates. Never infers. Never expands scope.
  Idempotent with Gate 10a.
- `CANONICAL_COMPOUND_CONTEXTS` is derived from
  `CONTEXT_NORMALIZATIONS.values()` at module load. It is the
  authority on canonical compounds. Do not hardcode compound
  contexts anywhere else.
- The composed string in Gate 7 Path B is **never re-normalized** —
  that would reintroduce FM-169 inside the FM-170 fix.

## Testing before push

Run in order. Do not push if any fails — report back instead.

```bash
# 1. Import check
python -c "import mnemos_lite; import belief_extractor; print('imports ok')"

# 2. Regression suite (12 FM tests, ~1s)
pytest tests/test_regression.py -v

# 3. Deterministic gate verification (74 checks)
python verify.py

# 4. If change touches L0–L4, L9, or L12–L15:
#    run mnemos_session.py for one short session,
#    confirm no regressions in the digest output.
```

CI runs checks 2 and 3 automatically on push to main
(`.github/workflows/ci.yml`). Do not rely on CI as a substitute
for running locally first.

## FM-169 — next priority (do not implement without Commander V review)

`normalize_context("monday mornings")` returns `"morning"` because dict
iteration matches the shorter `mornings → morning` key before
`monday mornings → monday_morning`. Fix direction: sort
`CONTEXT_NORMALIZATIONS` keys by length descending before iteration,
or replace substring matching with exact-key lookup. **Do not implement
until Commander V has reviewed the fix direction.**

## What to skip

- Don't reformat large blocks unrelated to the change.
- Don't "modernize" working code unsolicited.
- Don't add dependencies without asking.
- Don't touch Phase D or E layers (L3 async consolidation, L7, L10,
  L11, L16) until Phase C is complete.
