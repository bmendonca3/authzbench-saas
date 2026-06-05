# Live Baseline Refresh Panel Context

Date: 2026-06-05

Question:

Does replacing the legacy 15-task live HTTP scripted baseline with a current
44-task Docker-backed harness check improve AuthZBench-SaaS v0-candidate
credibility without overclaiming live-agent or leaderboard readiness?

## Current Repo State

AuthZBench-SaaS is still alpha/pre-v0. The updated goal is to build toward a
credible v0-candidate benchmark, while the strict v0 release gate must keep
reporting `v0_ready: false` until all real v0 requirements pass.

Current public split:

- 6 synthetic SaaS apps
- 44 public tasks
- 18 vulnerable tasks
- 26 secure controls
- 16 denial controls
- 10 authorized-allow controls

## Change Under Review

The previous `baselines/live-scripted-baseline-summary.json` was a legacy
15-task snapshot. This checkpoint reran the live HTTP scripted baseline against
the Docker targets on the current 44-task split and promoted only a compact
summary into the public repo.

Updated tracked files:

- `baselines/live-scripted-baseline-summary.json`
- `baselines/baseline-registry.json`
- `baselines/README.md`
- `docs/baseline-credibility.md`
- `docs/status.md`
- `docs/launch-report.md`
- `README.md`
- `CHANGELOG.md`
- `tests/test_baseline_registry.py`

The full generated run under `results/` and target logs under `captures/` remain
ignored and are not committed.

## Commands Run

Docker daemon preflight:

```bash
docker info --format '{{.ServerVersion}}'
```

Docker target and live baseline run:

```bash
rm -rf captures/request-logs results/live-scripted-baseline-current
mkdir -p captures/request-logs
docker compose up --build -d
python3 scripts/container_smoke.py
python3 -m authzbench.run \
  --task 'tasks/*/*.json' \
  --agent-cmd 'python3 scripts/live_scripted_baseline_agent.py' \
  --results-dir results/live-scripted-baseline-current \
  --timeout-seconds 10 \
  --benchmark-commit-sha "$(git rev-parse HEAD)" \
  --agent live_scripted_baseline_agent \
  --model deterministic-live-http-script \
  --harness-type scripted-live-http \
  --target-log-dir captures/request-logs
docker compose down
```

Focused validation:

```bash
python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_v0_release.py --allow-incomplete
```

## Observed Result

The Docker smoke passed.

The live HTTP scripted baseline passed all 44 public tasks:

- `task_count`: 44
- `passed_count`: 44
- `vulnerable_task_count`: 18
- `control_task_count`: 26
- `denial_control_task_count`: 16
- `authorized_allow_control_task_count`: 10
- `exploit_proven_success_rate`: 1.0
- `false_positive_rate`: 0.0
- `authorized_allow_pass_rate`: 1.0
- `target_request_correlated_task_count`: 18
- `target_request_coverage_rate`: 0.4091

Important caveat:

The deterministic live scripted agent only exercises submitted findings before
writing its submission. It submits findings for vulnerable tasks and no findings
for secure controls, so target-side request logs correlate for the 18 vulnerable
tasks but not for the 26 secure controls. This is a current live harness check,
not leaderboard-grade live-agent evidence.

The baseline registry passes, but still reports:

```text
v0_baseline_ready: false
```

because the repo still lacks repeated current real model baselines across at
least five model/agent families and lacks a current tool-agent baseline.

The v0 release audit still reports `v0_ready: false`.

## Review Focus

Please check:

- whether the updated baseline registry correctly treats this as a current
  public harness check, not a model baseline or leaderboard result
- whether docs avoid overclaiming live-proof or v0 readiness
- whether the target-request coverage caveat is clear enough
- whether any personal paths, private result bundles, raw logs, or private data
  are exposed in tracked files
- whether additional tests or validator checks are needed before committing this
  checkpoint
