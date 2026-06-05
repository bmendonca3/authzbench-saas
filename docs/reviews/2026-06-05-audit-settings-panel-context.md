# Sectional Panel Context: Audit/settings Surface And v0 Goal Refresh

Section under review: sixth SaaS app, audit/settings task family, public counts,
roadmap status, and rewritten project goal.

## Review Question

Does this checkpoint make AuthZBench-SaaS more credible as a future top
authorization benchmark while staying honest that the repo is still
alpha/pre-v0?

## Changed Scope

- Added `apps/audit_settings/` as the sixth synthetic SaaS app on port `8016`.
- Added seven public audit/settings tasks:
  - 3 vulnerable tasks:
    - `aud_bola_nimbus_reads_quasar_audit_log`
    - `aud_bfla_member_disables_sso`
    - `aud_bfla_member_downloads_audit_export`
  - 4 secure controls:
    - `aud_secure_cross_org_audit_control`
    - `aud_auditor_reads_own_audit_control`
    - `aud_admin_updates_security_settings_control`
    - `aud_auditor_downloads_export_control`
- Updated task counts from 5 apps / 37 tasks to 6 apps / 44 tasks.
- Updated control mix from 15 vulnerable / 22 controls to 18 vulnerable / 26
  controls.
- Updated control subtypes from 15 denial / 7 authorized-allow to 16 denial /
  10 authorized-allow.
- Rewrote the repo goal toward becoming one of the strongest public benchmarks
  for SaaS authorization reasoning, while keeping the current label
  alpha/pre-v0.
- Marked roadmap scope items complete only where this checkpoint actually
  satisfies them: six apps, 40-50 public tasks, audit/settings coverage, and at
  least 10 authorized-allow controls.

## Files To Review

- `apps/audit_settings/app.py`
- `tasks/audit_settings/*.json`
- `authzbench/core.py`
- `scripts/scripted_baseline_agent.py`
- `scripts/container_smoke.py`
- `tests/test_http_apps.py`
- `tests/test_validate_manifests.py`
- `tests/test_runner.py`
- `README.md`
- `ROADMAP.md`
- `docs/goal.md`
- `docs/status.md`
- `docs/benchmark-card.md`
- `docs/v0-release-plan.md`
- `docs/v0-task-build-matrix.md`
- `docs/launch-report.md`

## Verification Already Run

```bash
python3.11 -Wd -m unittest tests.test_http_apps tests.test_validate_manifests tests.test_harness tests.test_runner
python3.11 -m authzbench.validate_manifests --task 'tasks/*/*.json'
python3.11 -m compileall -q authzbench apps tests scripts
docker compose config
```

Result: all passed locally. Docker runtime smoke was not claimed; local Docker
daemon availability remains a separate release-readiness gap.

## Known Remaining v0 Gaps

- Private holdout pack is still not implemented.
- CI workflow remains blocked by missing workflow-scoped GitHub credentials.
- Docker runtime smoke still requires an available Docker daemon.
- Legacy Kiro/model baselines need reruns on the 44-task split.
- More route aliases, decoys, multi-seed private holdouts, and live-agent
  isolation are still v0 work.

## Requested Review Output

Return:

- top findings
- evidence
- confidence
- what to verify locally

Focus on task realism, benchmark uniqueness/value, overclaiming risk, scoring
credibility, and whether the roadmap/goal now communicate a serious path to a
top benchmark.
