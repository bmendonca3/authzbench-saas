# Panel Review Prompt: Leaderboard Artifact Validation

You are reviewing a benchmark repository section for AuthZBench-SaaS. Review
only the artifact-backed leaderboard validation slice described in:

`docs/reviews/2026-06-05-leaderboard-artifact-validation-panel-context.md`

Please inspect the relevant files if available:

- `scripts/validate_leaderboard_submission.py`
- `examples/leaderboard/scripted-sanity-public.leaderboard.json`
- `tests/test_leaderboard_submission.py`
- `scripts/validate_public.py`
- `docs/leaderboard-schema.md`
- `docs/v0-release-plan.md`

Return concise findings only:

- top correctness or benchmark-validity risks
- exact file/line or behavior evidence
- smallest fix
- whether this section is acceptable for alpha/pre-v0 after fixes

Do not edit files, mutate git, install dependencies, upload anything, or take
external actions.
