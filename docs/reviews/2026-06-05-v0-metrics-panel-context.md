# v0 Metrics Panel Context

Date: 2026-06-05

Section under review: scorer/runner result metrics and leaderboard schema.

## Question

Do the new v0-candidate run-summary metrics make AuthZBench-SaaS more credible
as a SaaS authorization benchmark without overclaiming that the alpha preview is
already v0 or leaderboard-ready?

## Changed Files

- `authzbench/score.py`
- `authzbench/run.py`
- `tests/test_runner.py`
- `tests/test_runner_request_logs.py`
- `docs/result-schema.md`
- `docs/leaderboard-schema.md`
- `docs/v0-release-plan.md`
- `docs/status.md`
- `ROADMAP.md`
- `README.md`
- `CHANGELOG.md`

## Parent-Verified Facts

- The repo is still alpha/pre-v0.
- Public task count is 44: 18 vulnerable tasks and 26 secure-control tasks.
- Secure controls include 16 denial controls and 10 authorized-allow controls.
- The old `mean_score` remains for alpha compatibility.
- New run-summary fields include:
  - `v0_metric_profile`
  - `v0_passed_count`
  - `v0_mean_score`
  - `exploit_proven_task_count`
  - `vulnerable_full_pass_count`
  - `boundary_reasoning_pass_rate`
  - `vulnerable_safety_pass_rate`
  - `control_false_report_count`
  - `control_false_report_rate`
  - `control_execution_pass_rate`
  - `invalid_submission_count`
  - `invalid_submission_rate`
  - `target_request_correlated_task_count`
  - `target_request_coverage_rate`
- Per-task summary records now include:
  - `submission_finding_count`
  - `invalid_submission`
  - `control_replay_passed`
  - task-level subscore fields
- `control_execution_pass_rate` is based on backend control replay, while
  `control_false_report_rate` is based on whether the agent reported findings on
  secure controls.
- `v0_mean_score` avoids giving vulnerable-task credit for agent-independent
  secure-control replay. Vulnerable-task control replay remains an integrity
  gate: if benchmark controls fail, the task does not pass v0-candidate scoring.
- Missing, malformed, or unscorable submissions are tracked separately through
  invalid-submission metrics.

## Verification Already Run

```bash
python3 -Wd -m unittest discover -s tests -p 'test_runner*.py'
python3 scripts/validate_public.py --include-scripted-baseline
```

Results:

- focused runner tests passed: 6 tests before panel fixes and should be rerun
  after the accepted panel findings are addressed
- public validation passed: 42 tests, manifest validation, compile checks,
  Docker Compose config validation, Git-tracked privacy scan, and scripted
  baseline
- manifest validation reported 44 public tasks, 18 vulnerable, 26 controls,
  16 denial controls, 10 authorized-allow controls, and 0 private holdouts

## Known Remaining v0 Gaps

- Private holdouts and protected holdout execution are still missing.
- CI workflow is still absent.
- Docker runtime smoke and Docker-backed live-agent correlation still need
  current validation when a daemon is available.
- Repeated real model/agent baselines on the current 44-task split are still
  required.
- A final release-readiness panel review is still required before any v0 claim.
