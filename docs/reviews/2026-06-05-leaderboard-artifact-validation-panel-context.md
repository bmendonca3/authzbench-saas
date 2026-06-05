# Leaderboard Artifact Validation Panel Context

Date: 2026-06-05

Section under review: baseline methodology and leaderboard schema, specifically
artifact-backed validation for leaderboard submission rows.

## Objective

AuthZBench-SaaS should not accept leaderboard rows that are only hand-entered
aggregates. This slice adds an optional `source_run_summary` field and a public
validation gate that requires tracked examples to cross-check against a source
run summary.

## Files Changed

- `scripts/validate_leaderboard_submission.py`
- `examples/leaderboard/scripted-sanity-public.leaderboard.json`
- `tests/test_leaderboard_submission.py`
- `tests/test_validate_public.py`
- `scripts/validate_public.py`
- `docs/leaderboard-schema.md`
- `docs/status.md`
- `docs/v0-release-plan.md`
- `docs/publish-checklist.md`
- `README.md`
- `ROADMAP.md`
- `CHANGELOG.md`

## Current Behavior

- `source_run_summary` may point to a relative `summary.json`-style artifact.
- `--require-source-summary` makes that field mandatory for each submission.
- The validator rejects absolute `source_run_summary` paths.
- The validator compares overlapping aggregate fields between the submission
  and source summary, including agent, model, harness type, benchmark version,
  commit SHA, task counts, v0 metrics, false-positive metrics, and target
  request coverage.
- If the source summary contains `run_id`, it must match the submission.
- If an older alpha source summary lacks `run_id`, the validator warns that
  identity cross-checking is limited.
- If the source summary contains per-task `tasks`, the validator recomputes
  aggregate summary metrics from those rows and rejects inconsistencies.
- The tracked public example references
  `baselines/scripted-baseline-summary.json` and remains
  `leaderboard_eligible: false`.
- `scripts/validate_public.py` now runs:

```bash
python3 scripts/validate_leaderboard_submission.py \
  --submission examples/leaderboard/*.json \
  --require-source-summary
```

## Verification Already Run

```bash
python3 -Wd -m unittest discover -s tests -p 'test_leaderboard_submission.py'
python3 -Wd -m unittest discover -s tests -p 'test_validate_public.py'
python3 scripts/validate_leaderboard_submission.py --submission 'examples/leaderboard/*.json' --require-source-summary
```

All three passed before panel review.

## Known Limits

- The tracked scripted baseline source summary is an older aggregate summary and
  lacks `run_id`, so the validator warns rather than treating that alpha-only
  row as identity-complete.
- This does not yet validate release-candidate private holdout bundles because
  real private holdouts and protected execution are still future work.
- This does not replace repeated real model baselines or a tool-agent baseline.
