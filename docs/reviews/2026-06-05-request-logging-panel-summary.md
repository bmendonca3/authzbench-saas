# Request Logging Sectional Panel Summary

Date: 2026-06-05

## Verdict

Accepted for alpha/pre-v0.

The request-logging slice is a useful credibility improvement because it gives
the Docker HTTP targets their own request record instead of relying only on
scorer-owned replay transcripts. It remains correctly positioned as alpha work:
the repo does not claim leaderboard-grade live-target proof until request logs
are correlated into per-task runner artifacts.

## Panel Findings

### Medium: log I/O could break target responses

The first implementation wrote target logs inline without fault isolation. A
bad mount or unwritable log path could make a benchmark target fail for reasons
unrelated to the task.

Disposition: fixed before commit by making request-log writes best-effort.

### Medium: Docker logs could become root-owned on Linux hosts

The Compose bind mount writes logs back to the host. On Linux, a root-running
container can produce host files that are awkward for the runner to clean up.

Disposition: mitigated before commit by running Compose services as a
configurable numeric user, defaulting to `1000:1000`, and documenting the
`AUTHZBENCH_DOCKER_UID` / `AUTHZBENCH_DOCKER_GID` override.

### Low: stale docs said live-target logging was still missing

Several docs initially still described request logging as planned or missing
after the implementation existed. Those lines were corrected to say Docker
target-side JSONL logs exist in the alpha, while real v0 still needs per-task
correlation into `target-requests.jsonl`.

Disposition: fixed before commit.

### Residual v0 gap: logs are app-level, not task-artifact-level

The logs currently live under `captures/request-logs/` and are useful for Docker
target inspection. For v0, the runner should extract only relevant request
records and write them into each task result directory.

Disposition: partially improved before commit by adding optional `task_id`,
`run_id`, and `agent_id` fields to target-side logs and teaching the live
scripted baseline/container smoke to send them. Full per-task artifact
correlation remains a roadmap/release-gate item.

### Low: container smoke checked existence more than fidelity

The first smoke-script update checked that request logs existed and were
non-empty, but not that the expected task requests appeared in the correct app
log.

Disposition: fixed before commit by requiring matching `task_id`, status, seed,
run id, and agent id entries for each Docker smoke request.

### Residual v0 gap: Docker runtime smoke was not available locally

`docker compose config` passed, but Docker daemon access was unavailable on the
local machine, so container runtime logging must still be checked from a machine
with Docker available or in CI.

Disposition: documented as a verification gap.

## Local Verification

- `python3 -Wd -m unittest discover -s tests`
- `python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'`
- `python3 -m compileall -q authzbench apps tests scripts`
- `python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/scripted_baseline_agent.py' --results-dir results/request-log-final-smoke --timeout-seconds 10 --benchmark-commit-sha "$(git rev-parse HEAD)" --agent scripted_baseline_agent --model deterministic-script --harness-type scripted`
- `git diff --check`
- `docker compose config`

## V0 Follow-Up

- Add runner-side request correlation into each task's `target-requests.jsonl`.
- Include `run_id`, `task_id`, and `agent_id` consistently in all live HTTP
  agent paths.
- Add CI or release validation that runs Docker targets and confirms request-log
  entries are produced.
- Keep raw response bodies out of target logs unless a future privacy review
  explicitly allows a redacted artifact format.
