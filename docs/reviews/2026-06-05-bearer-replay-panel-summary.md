# Bearer Replay Scorer Review Summary

Review date: 2026-06-05

Question: Does the API-token scorer replay now treat seeded bearer-token
evidence as first-class proof while preserving legacy actor-compatible replay?

## Review Scope

This was a bounded parent/direct sectional review. The live agent pool was at
its thread limit, so no additional subagent reviewer was spawned for this
section. The review used direct code inspection plus targeted and full
validation commands.

## Findings

- Accepted: API-token evidence can now be scored with only
  `request.headers.Authorization: Bearer <seeded token>`.
- Accepted: actor-only replay remains compatible for existing task manifests and
  scripted baselines.
- Accepted: if `actor` and bearer token are both supplied, they must resolve to
  the same seeded actor. Unknown or mismatched tokens fail closed instead of
  receiving exploit credit.
- Accepted: docs now distinguish this scorer-side hardening from the remaining
  live-agent and leaderboard execution requirements.

## Evidence

- `authzbench/core.py` resolves optional replay headers and maps bearer tokens
  through seeded public actors.
- `tests/test_harness.py` includes positive bearer replay, unknown-token
  failure, and actor/token mismatch failure cases.
- `docs/result-schema.md` documents optional replay headers and the fail-closed
  bearer semantics.

Verification run:

```bash
python3.11 -Wd -m unittest tests.test_harness
python3.11 scripts/validate_public.py --include-scripted-baseline
```

The full public validation passed with 41 tests and a 44/44 scripted baseline.

## Remaining v0 Risk

This removes the specific "first-class scored bearer-token replay" gap for the
API-token target. It does not complete real v0. The benchmark still needs
protected private-holdout execution, unpublished human-designed holdouts,
Docker-backed live-agent isolation, repeated real model baselines, stronger
route alias/randomization, and final release-readiness review.
