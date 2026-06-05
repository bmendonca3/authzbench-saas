# Request Logging Sectional Panel Prompt

Date: 2026-06-05

Review the request-logging slice for AuthZBench-SaaS alpha/pre-v0.

Read:

- `docs/reviews/2026-06-05-request-logging-panel-context.md`
- the current git diff for the files in scope

Scope:

- `apps/request_logging.py`
- `apps/project_mgmt/app.py`
- `apps/billing/app.py`
- `docker-compose.yml`
- `scripts/container_smoke.py`
- `tests/test_http_apps.py`
- related documentation updates

Questions:

1. Does the slice improve benchmark credibility without overstating v0 readiness?
2. Are target-side request logs useful, privacy-aware, and bounded enough for the alpha?
3. Do docs distinguish alpha Docker logs from the future v0 requirement to correlate logs into per-task runner artifacts?
4. What must still be done before leaderboard-grade v0 live-target proof?

Reviewers should return findings with severity, evidence, and concrete fixes.
