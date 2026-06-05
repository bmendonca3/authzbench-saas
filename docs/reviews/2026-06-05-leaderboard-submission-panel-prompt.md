# Panel Prompt: Leaderboard Submission Validation

You are reviewing AuthZBench-SaaS in grounded read-only mode.

Read:

- `docs/reviews/2026-06-05-leaderboard-submission-panel-context.md`
- `scripts/validate_leaderboard_submission.py`
- `examples/leaderboard/scripted-sanity-public.leaderboard.json`
- `tests/test_leaderboard_submission.py`
- `docs/leaderboard-schema.md`
- `docs/v0-release-plan.md`
- `ROADMAP.md`

Question: does this leaderboard submission validation section improve benchmark
credibility without overclaiming v0 or leaderboard readiness?

Return concise findings only:

- `Verdict`
- `Must fix before commit`
- `Should fix before v0`
- `Evidence`

Focus on whether the validator properly separates schema-valid evidence from
leaderboard eligibility, and whether it catches public-only, harness-check,
one-off, inconsistent-metric, and missing-live-evidence overclaims.

Do not edit files, write files, install dependencies, mutate Git state, browse
the web, or take external actions.
