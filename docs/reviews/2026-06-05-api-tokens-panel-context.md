# API-Tokens Expansion Panel Context

## Review Question

Does the new API-token target make AuthZBench-SaaS meaningfully stronger as an
alpha/pre-v0 authorization benchmark, and what must be fixed before this section
is committed?

## Parent-Verified State

- Repository: `authzbench-saas`
- Branch: `v0-hardening`
- GitHub remote: `https://github.com/bmendonca3/authzbench-saas.git`
- Current public split after this draft: 5 apps, 37 tasks, 15 vulnerable tasks,
  22 controls
- New app: `apps/api_tokens/`, port `8015`
- New task directory: `tasks/api_tokens/`
- New vulnerable classes:
  - tenant-bound token reads another tenant's secret
  - read-only token updates a restricted secret
  - token without export scope reads admin export
- New controls:
  - secure cross-tenant token denial
  - secure read-token write denial
  - secure missing-export-scope denial
  - authorized same-tenant write token update
  - authorized export-token read

## Verification Already Run

```bash
python3.11 -Wd -m unittest tests.test_http_apps tests.test_validate_manifests tests.test_harness tests.test_runner
python3.11 -m authzbench.validate_manifests --task 'tasks/*/*.json'
git diff --check
```

Result: 24 tests passed. Manifest validation passed with 37 manifests, 15
vulnerable tasks, 22 controls, and zero private holdouts.

## Files To Inspect

- `apps/api_tokens/app.py`
- `tasks/api_tokens/*.json`
- `authzbench/core.py`
- `scripts/scripted_baseline_agent.py`
- `scripts/container_smoke.py`
- `tests/test_http_apps.py`
- `tests/test_harness.py`
- `tests/test_validate_manifests.py`
- `tests/test_runner.py`
- current docs/count updates in `README.md`, `ROADMAP.md`,
  `docs/v0-task-build-matrix.md`, `docs/status.md`, and
  `docs/launch-report.md`

## Known Limits

- This is still a public alpha split, not a private leaderboard split.
- API-token scorer replay remains compatible with the benchmark actor field.
  The HTTP target also accepts seeded `Authorization: Bearer ...` tokens when
  the actor header is absent.
- Secure routes still use an obvious `/api/secure/...` naming convention.
- Full public validation, tracked baseline refresh, privacy scan, push, and
  fresh-clone validation have not yet run for this section.
