# Docker Runtime CI Panel Context

Date: 2026-06-05

Question: Does the Docker runtime CI change make meaningful, honest progress
toward v0 by proving the public Docker targets boot and emit target-side request
logs, without overclaiming local Docker success or v0 readiness?

Changed files:

- `.github/workflows/validate.yml`
- `scripts/validate_public.py`
- `tests/test_ci_workflow.py`
- `tests/test_validate_public.py`
- `README.md`
- `ROADMAP.md`
- `docs/status.md`
- `docs/publish-checklist.md`
- `docs/v0-release-plan.md`
- `CHANGELOG.md`

Implementation summary:

- Added `--include-container-smoke` to `scripts/validate_public.py`.
- The new flag runs `docker compose up --build -d`, then
  `python scripts/container_smoke.py`, then always attempts
  `docker compose down`.
- The smoke wrapper checks that the Docker CLI exists before starting.
- CI now runs:

```bash
python scripts/validate_public.py --include-scripted-baseline --include-container-smoke
```

- CI timeout increased from 15 to 25 minutes.
- `tests/test_ci_workflow.py` now asserts the top-level `jobs:` key, the
  container-smoke validation command, and the 25-minute timeout.
- `tests/test_validate_public.py` checks Docker-missing behavior, cleanup on
  smoke failure, and that the smoke runs only when requested.

Parent-verified local checks:

```bash
python3 -Wd -m unittest discover -s tests -p 'test_validate_public.py'
python3 -Wd -m unittest discover -s tests -p 'test_ci_workflow.py'
python3 -m compileall -q scripts tests
python3 scripts/validate_public.py --include-scripted-baseline
```

Results:

- Focused tests passed.
- Full non-container public validation passed with 49 tests, manifest
  validation, compile checks, Docker Compose config validation, privacy scan, and
  the 44/44 deterministic scripted baseline.
- Local Docker daemon was unavailable:

```text
failed to connect to the docker API at the local user Docker socket
```

So the actual container-smoke runtime proof must come from GitHub Actions after
push.

Known remaining v0 blockers after this change:

- real private holdout tasks and protected execution
- route-alias randomization and private-holdout decoy variation
- isolated/containerized model-agent execution for leaderboard runs
- repeated real model baselines on the current 44-task split
- final release-readiness panel review
