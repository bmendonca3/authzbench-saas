# Docker Runtime CI Panel Summary

Date: 2026-06-05

Section reviewed:

- public validation script
- GitHub Actions validation workflow
- Docker container smoke gate
- release/status wording around Docker runtime proof

Question:

Does the Docker runtime CI change make meaningful, honest progress toward v0 by
proving the public Docker targets boot and emit target-side request logs, without
overclaiming local Docker success or v0 readiness?

## Reviewers Counted

- Gemini 3.5 Flash (High), verified from Antigravity log.
- Gemini 3.1 Pro (High), verified from Antigravity log.
- internal code/runtime auditor.
- internal docs/release wording auditor.

Limited or unavailable:

- Claude Sonnet 4.6 (Thinking) label was verified in the Antigravity log, but no
  usable final findings were returned.
- Claude Opus 4.6 (Thinking) label was verified in the Antigravity log, but no
  usable final findings were returned.
- Kiro was not used for this bounded section review.

Raw Antigravity logs are under the ignored
`docs/reviews/panel-logs/docker-runtime-ci-20260605/` directory.

## Findings And Disposition

### Accepted: run Docker runtime smoke in CI

Reviewers agreed that the previous CI gate only validated Docker Compose syntax.
The workflow now runs:

```bash
python scripts/validate_public.py --include-scripted-baseline --include-container-smoke
```

The `--include-container-smoke` flag starts the Compose stack, runs
`scripts/container_smoke.py`, and tears the stack down.

### Accepted: avoid bind-mount permission failures

The code reviewer and Gemini 3.5 flagged a Linux-runner risk: Docker targets
write JSONL logs to `captures/request-logs`, and mismatched container/host UIDs
could make the logs missing or unwritable.

Disposition:

- `run_container_smoke()` now pre-creates `captures/request-logs`.
- It sets `AUTHZBENCH_DOCKER_UID` and `AUTHZBENCH_DOCKER_GID` from the host
  process when those APIs are available.
- This was preferred over `chmod 777`, which was rejected as broader than needed.

### Accepted: avoid Compose project collisions

The code reviewer noted that fresh-clone validation uses a deterministic temp
directory name and could collide with another local `authzbench-saas` Compose
stack.

Disposition:

- `run_container_smoke()` now uses a unique Compose project name:
  `authzbench-public-smoke-<pid>`.
- The same project name is used for `up`, `logs`, and `down`.

### Accepted: make CI failures debuggable

Gemini 3.5 recommended logging container output before teardown when the smoke
script fails.

Disposition:

- On smoke failure, validation now runs:

```bash
docker compose -p <project> logs --no-color --tail 200
```

- Teardown still runs afterward.

### Accepted: stale Docker wording

The docs reviewer found stale wording that still described Docker-backed CI as a
future need.

Disposition:

- `README.md` now says CI runs Docker container smoke, while leaderboard-grade
  live-agent proof still needs isolated execution and broader repeated model
  coverage.
- `docs/launch-report.md` now says the public GitHub Actions workflow runs
  Docker container smoke, while manual local smoke reruns still require a Docker
  daemon.

### Accepted: new tests must be tracked

Gemini 3.1 and the code reviewer noted that `tests/test_validate_public.py` was
untracked during review.

Disposition:

- The file is intentionally part of this section change and must be staged with
  the commit.

### Deferred: skip Docker Compose config when Docker is absent

Gemini 3.5 suggested making standard public validation skip Docker Compose config
when Docker is unavailable.

Disposition:

- Deferred. Docker Compose config validation remains part of the public gate.
  This benchmark is built around Dockerized targets, so a public release check
  should fail plainly when Docker tooling is absent.
- The new container-smoke flag does add a clearer Docker CLI error before trying
  runtime smoke.

## Verification

Parent-run checks after fixes:

```bash
python3 -Wd -m unittest discover -s tests -p 'test_validate_public.py'
python3 -Wd -m unittest discover -s tests -p 'test_ci_workflow.py'
python3 -m compileall -q scripts tests
python3 scripts/validate_public.py --include-scripted-baseline
git diff --check
```

Results:

- focused validation-script tests passed
- focused workflow test passed
- compile checks passed
- full non-container public validation passed with 49 tests, manifest
  validation, compile checks, Docker Compose config validation, privacy scan, and
  the 44/44 deterministic scripted baseline
- `git diff --check` passed

Local Docker runtime smoke was not run because the local Docker daemon was not
available. The release-gate proof for container runtime behavior must come from
the pushed GitHub Actions run.

## Remaining V0 Blockers

This section reduces the Docker runtime-smoke blocker, but it does not finish the
benchmark. The real v0 still needs:

- protected private holdouts outside public Git history
- private route-alias randomization and decoy variation
- isolated/containerized agent execution for leaderboard runs
- repeated real-model baselines on the current task split
- final release-readiness panel review
