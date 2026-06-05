# Runner Correlation Sectional Panel Prompt

Date: 2026-06-05

Review the runner-side target request correlation slice for AuthZBench-SaaS
alpha/pre-v0.

Read:

- `docs/reviews/2026-06-05-runner-correlation-panel-context.md`
- the current git diff for the files in scope

Scope:

- `authzbench/run.py`
- `scripts/live_scripted_baseline_agent.py`
- `tests/test_runner_request_logs.py`
- result-schema, roadmap, status, launch, benchmark-card, and README updates

Questions:

1. Does `--target-log-dir` correctly improve live-target proof without changing
   deterministic scoring?
2. Does the runner filter target logs narrowly enough for alpha use?
3. Are the docs honest about what is now implemented versus what still belongs
   to real v0/leaderboard validation?
4. What issues should be fixed before this slice is committed?

Return findings with severity, evidence, and concrete fixes.
