# Result Schema

`python3 -m authzbench.run` writes one result directory per benchmark run:

```text
results/<run_id>/
  summary.json
  <task_id>/
    context.json
    submission.json
    agent.json
    score.json
    transcript.json
    target-requests.jsonl  # v0 target shape; alpha Docker logs live under captures/request-logs/
```

## `context.json`

Rendered task context given to the agent:

- `task_id`
- `app`
- `seed`
- `policy`
- `objective`
- `allowed_hosts`
- `target`
- `actors`
- `refs`
- `api_docs`
- `output_schema`

`target` includes the local `base_url`, Docker-network `container_base_url`,
required seed header, and task seed. Agents that use live HTTP tools should send
the `x-authzbench-seed` header so the container state matches the rendered task.

## `submission.json`

The agent-created structured finding file:

- `findings`: list of findings
- vulnerable tasks should contain exactly one primary finding
- secure-control tasks should use `findings: []`

## `agent.json`

Runner metadata:

- `command`
- `returncode`
- `duration_seconds`
- `stdout`
- `stderr`

## `score.json`

Task score:

- `passed`
- `score`
- `subscores.exploit_proof`
- `subscores.boundary_reasoning`
- `subscores.false_positive_control`
- `subscores.safety`
- `observations`
- `transcript`

For vulnerable tasks, `boundary_reasoning` requires the finding claim and the
submitted `boundary` object to match the task's expected attacker/tenant/role
boundary.

## `transcript.json`

Scorer-owned backend replay transcript. Each entry has:

- `name`: `proof` or the control name
- `request`: actor, method, path, and optional body
- `response`: status and JSON body returned by the benchmark app logic

## Target-Side Request Logs

When the Docker targets are run through the provided Compose file, the target
apps write JSONL logs under `captures/request-logs/`. Each entry includes:

- `request_id`
- `timestamp_unix`
- `app`
- `seed`
- `actor`
- `method`
- `path`
- `status`
- `response_body_sha256`
- optional `run_id`
- optional `agent_id`
- optional `task_id`

When `python3 -m authzbench.run` is called with `--target-log-dir`, the runner
records the relevant app log offset before each task starts, then filters only
newly appended entries by `run_id`, `task_id`, and `agent_id`. Matching entries
are written into the task's `target-requests.jsonl` artifact. Scoring still
comes from deterministic replay in `transcript.json`.

If `--target-log-dir` is omitted, the runner does not create
`target-requests.jsonl`.

The runner does not expose `AUTHZBENCH_TARGET_LOG_DIR` to the agent process.
Leaderboard-grade runs should still isolate the agent from the target-log
filesystem path so the artifact remains target-side evidence rather than
self-reported output.

## `summary.json`

Run-level aggregate:

- `run_id`
- `benchmark_version`
- `benchmark_commit_sha`
- `agent_cmd`
- `agent`
- `model`
- `harness_type`
- `target_log_dir`
- `timeout_seconds`
- `task_count`
- `passed_count`
- `mean_score`
- `vulnerable_task_count`
- `control_task_count`
- `denial_control_task_count`
- `authorized_allow_control_task_count`
- `exploit_proven_success_rate`
- `false_positive_rate`
- `authorized_allow_pass_rate`
- per-task score records

Each per-task summary record includes `control_type` for secure-control tasks.
The value is `denial` when the correct behavior is a blocked request, and
`authorized_allow` when the correct behavior is permitted access with no finding.

When `--target-log-dir` is supplied, each per-task summary record also includes:

- `target_request_count`
- optional `target_request_warning`, such as `target_log_missing` or
  `no_target_requests_correlated`
