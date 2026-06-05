# Panel Prompt: Baseline Registry Credibility

You are reviewing AuthZBench-SaaS in grounded read-only mode.

Read:

- `docs/reviews/2026-06-05-baseline-registry-panel-context.md`
- `scripts/validate_baseline_registry.py`
- `baselines/baseline-registry.json`
- `tests/test_baseline_registry.py`
- `docs/baseline-credibility.md`
- `docs/leaderboard-schema.md`
- `ROADMAP.md`

Question: does this baseline-registry section improve benchmark credibility
without overclaiming v0, leaderboard, or top-benchmark readiness?

Return concise findings only:

- `Verdict`
- `Must fix before commit`
- `Should fix before v0`
- `Evidence`

Focus on whether stale/legacy runs, one-off model runs, harness checks, repeated
run evidence, and leaderboard eligibility are separated clearly enough for a
public benchmark repo.

Do not edit files, write files, install dependencies, mutate Git state, browse
the web, or take external actions.
