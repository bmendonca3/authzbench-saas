# Private Leaderboard Submission Panel Context

Section: baseline methodology and leaderboard schema.

AuthZBench-SaaS remains alpha/pre-v0. This slice adds the first
release-candidate private-holdout leaderboard row, but it must not be treated as
a finished leaderboard launch or a strong model-performance claim.

## Change Under Review

- Added `leaderboard_sources/haiku-private-holdout-20260605-redacted-source-summary.json`.
- Added `leaderboard_submissions/2026-06-05/haiku-private-holdout.leaderboard.json`.
- Added a current release-candidate fixture test in
  `tests/test_leaderboard_submission.py`.
- Updated public docs to say the leaderboard-submissions gate now passes while
  strict v0 remains blocked by sectional reviews and release evidence.

## Private Run Evidence

Two ignored local private-holdout runs were executed with the benchmark runner
and `scripts/kiro_baseline_agent.py --model claude-haiku-4.5`. The raw result
bundles and private task manifests remain ignored and untracked.

Both runs had the same aggregate metrics:

- `task_count`: 24
- `vulnerable_task_count`: 12
- `control_task_count`: 12
- `denial_control_task_count`: 6
- `authorized_allow_control_task_count`: 6
- `v0_passed_count`: 12
- `v0_mean_score`: 0.5
- `exploit_proven_task_count`: 0
- `exploit_proven_success_rate`: 0.0
- `vulnerable_full_pass_count`: 0
- `false_positive_rate`: 0.0
- `control_false_report_rate`: 0.0
- `invalid_submission_count`: 0
- `invalid_submission_rate`: 0.0
- `run_count`: 2
- `variance_or_ci`: `stddev=0.0000`

Interpretation: this is weak model evidence but clean leaderboard-pipeline
evidence. It shows a repeated, non-scripted, private-holdout-only model row can
be validated without publishing the private tasks or raw run outputs.

## Privacy Boundary

Tracked artifacts must not include:

- private task IDs
- private task paths
- private seeds
- hidden refs
- routes
- oracle bodies
- prompt text
- transcripts
- raw Kiro output
- local result paths
- private filesystem details

The tracked source summary intentionally contains aggregate counts and metrics
only.

## Current Validation

```bash
python3 -Wd -m unittest discover -s tests -p 'test_leaderboard_submission.py'
python3 -Wd -m unittest discover -s tests -p 'test_v0_release_validator.py'
python3 scripts/validate_leaderboard_submission.py --submission 'leaderboard_submissions/**/*.json' --require-source-summary
python3 scripts/validate_v0_release.py --allow-incomplete
```

Current strict audit result:

- `leaderboard_submissions`: passed
- `release_candidate_submission_count`: 1
- `release_candidate_leaderboard_eligible_count`: 1
- `v0_ready`: false

Remaining blockers:

- not all required sectional reviews are marked v0-ready
- `docs/release-evidence.json` fields remain false
- protected/isolated leaderboard execution still needs release evidence
