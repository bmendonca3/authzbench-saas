# File-Sharing Expansion Panel Context

## Review Question

Does the new file-sharing target make AuthZBench-SaaS meaningfully stronger as
an alpha/pre-v0 authorization benchmark, and what must be fixed before this
section is committed?

## Parent-Verified State

- Repository: `authzbench-saas`
- Branch: `v0-hardening`
- GitHub remote: `https://github.com/bmendonca3/authzbench-saas.git`
- Current public split after this draft: 4 apps, 29 tasks, 12 vulnerable tasks,
  17 controls
- New app: `apps/file_sharing/`, port `8014`
- New task directory: `tasks/file_sharing/`
- New vulnerable classes:
  - cross-workspace file read
  - expired share link still resolving
  - viewer creating public share links
- New controls:
  - secure cross-workspace denial
  - secure expired-link denial
  - secure viewer-share denial
  - same-workspace authorized file read
  - active public share-link authorized read

## Verification Already Run

```bash
python3.11 -Wd -m unittest tests.test_http_apps tests.test_validate_manifests tests.test_harness tests.test_runner
python3.11 -m authzbench.validate_manifests --task 'tasks/*/*.json'
```

Result: 23 tests passed. Manifest validation passed with 29 manifests, 12
vulnerable tasks, 17 controls, and zero private holdouts.

## Files To Inspect

- `apps/file_sharing/app.py`
- `tasks/file_sharing/*.json`
- `authzbench/core.py`
- `scripts/scripted_baseline_agent.py`
- `scripts/container_smoke.py`
- `tests/test_http_apps.py`
- `tests/test_harness.py`
- `tests/test_validate_manifests.py`
- `tests/test_runner.py`

## Known Limits

- This is still a public alpha split, not a private leaderboard split.
- Secure routes still use an obvious `/api/secure/...` naming convention.
- The deterministic scripted baseline is a harness sanity check, not a model
  score.
- Full public validation, Docker config validation, privacy scan, and fresh-clone
  validation have not yet run for this section.
