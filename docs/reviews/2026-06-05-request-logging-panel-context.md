# Request Logging Sectional Panel Context

Date: 2026-06-05

AuthZBench-SaaS is currently an alpha/pre-v0 public benchmark scaffold, not the
real v0 release. The current public split is two toy SaaS apps and fifteen
tasks.

This slice adds an alpha target-side request logging mechanism:

- Docker targets receive `AUTHZBENCH_REQUEST_LOG_DIR=/bench/captures/request-logs`.
- Compose mounts `./captures/request-logs` into each target container.
- HTTP handlers log one JSONL record per request when logging is enabled.
- Logs contain method, path, actor, seed, status, app, timestamp, request id,
  optional run/agent ids, and a SHA-256 hash of the response body.
- Raw response bodies are not written to target logs.
- The alpha Docker logs stay under `captures/request-logs/`.
- The docs explicitly say real v0 still needs per-task correlation into
  `target-requests.jsonl` artifacts.

Verification before panel synthesis:

- `python3 -Wd -m unittest discover -s tests` passed, 16 tests.
- `python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'` passed,
  15 manifests.
- `python3 -m compileall -q authzbench apps tests scripts` passed.
- Scripted baseline smoke passed 15/15.
- `git diff --check` passed.
- `docker compose config` passed.
- Docker daemon was unavailable locally, so container runtime smoke could not be
  executed on this machine.
- Privacy/stale-wording scan over tracked content, excluding generated result
  and capture folders, returned no matches.

Known limitation:

This slice proves the target apps can emit request logs. It does not yet prove
that the runner copies and correlates only the current task's target-side
requests into the scored result directory.
