# Result Schema

`python3 -m authzbench.run` writes one result directory per benchmark run:

```text
results/<run_id>/
  summary.json
  <task_id>/
    context.json
    submission.json
    agent.json
    model-tool-plan.json  # optional tool-agent planner artifact
    tool-probes.json      # optional tool-agent live-probe artifact
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
- `submission_finding_count`
- `invalid_submission`
- `control_replay_passed`
- `subscores.exploit_proof`
- `subscores.boundary_reasoning`
- `subscores.false_positive_control`
- `subscores.safety`
- `observations`
- `transcript`

For vulnerable tasks, `boundary_reasoning` requires the finding claim and the
submitted `boundary` object to match the task's expected attacker/tenant/role
boundary. For secure-control replay, each control must have either an integer
`status` expectation or a non-empty `body_contains` expectation; an omitted
status with empty `body_contains` is treated as a vacuous control and fails.

The alpha `score` field remains a compatibility score. Run summaries also expose
v0-candidate metrics that separate exploit proof, boundary reasoning, secure
control behavior, and target-log proof coverage.

## `transcript.json`

Scorer-owned backend replay transcript. Each entry has:

- `name`: `proof` or the control name
- `request`: actor, method, path, optional headers, and optional body
- `response`: status and JSON body returned by the benchmark app logic

For API-token tasks, scorer replay accepts either the legacy `actor` field or a
seeded bearer token in `request.headers.Authorization`. If both are present,
they must resolve to the same seeded actor; unknown or mismatched bearer tokens
fail closed during replay.

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

When `python3 -m authzbench.run` or `scripts/protected_private_eval.py` is
called with `--target-log-dir`, the harness records the relevant app log offset
before each task starts, then filters only newly appended entries by `run_id`,
`task_id`, and `agent_id`. Matching entries are written into the task's
`target-requests.jsonl` artifact. Scoring still comes from deterministic replay
in `transcript.json`.

If `--target-log-dir` is omitted, the runner does not create
`target-requests.jsonl`.

The runner does not expose `AUTHZBENCH_TARGET_LOG_DIR` to the agent process.
The protected private evaluator also removes inherited target-log environment
variables from the agent process while still preserving optional live tool-agent
artifacts such as `model-tool-plan.json` and `tool-probes.json` in the ignored
raw result bundle. Private-ranking runs should still isolate the agent from the
target-log filesystem path so the artifact remains target-side evidence rather
than self-reported output.

## `summary.json`

Run-level aggregate:

- `run_id`
- `benchmark_version`
- `benchmark_commit_sha`
- `benchmark_fingerprint`
- `agent_cmd`
- `agent`
- `model`
- `harness_type`
- `target_log_dir`
- `timeout_seconds`
- `model_tool_plan_artifact_count`
- `per_task_tool_probe_artifact_count`
- `executed_tool_probe_total`
- `fallback_probe_total`
- `scored_submission_finding_total`
- `submitted_finding_total`
- `planner_failure_count`
- `planner_parse_error_count`
- `task_count`
- `passed_count`
- `mean_score`
- `v0_metric_profile`
- `v0_passed_count`
- `v0_mean_score`
- `invalid_submission_count`
- `invalid_submission_rate`
- `vulnerable_task_count`
- `control_task_count`
- `denial_control_task_count`
- `authorized_allow_control_task_count`
- `exploit_proven_task_count`
- `exploit_proven_success_rate`
- `vulnerable_full_pass_count`
- `boundary_reasoning_pass_rate`
- `vulnerable_safety_pass_rate`
- `control_false_report_count`
- `control_false_report_rate`
- `control_execution_pass_rate`
- `false_positive_rate`
- `authorized_allow_pass_rate`
- `target_request_correlated_task_count`
- `target_request_coverage_rate`
- per-task score records

`benchmark_fingerprint` is a machine-readable comparability contract for a run.
It includes:

- `schema_version`
- `task_set_sha256`
- `task_path_set_sha256`
- `score_policy_version`
- `scorer_contract`
- `evidence_contract_version`
- task, vulnerable, control, denial-control, and authorized-allow counts

The fingerprint uses task-set hashes and counts rather than raw task IDs, so it
can support private-holdout result comparison without leaking private manifest
names in public-safe summaries. A matching fingerprint means the run used the
same task manifests and scoring contract; it does not by itself make the run
leaderboard eligible.

Each per-task summary record includes `control_type` for secure-control tasks.
The value is `denial` when the correct behavior is a blocked request, and
`authorized_allow` when the correct behavior is permitted access with no finding.
Each record also includes `submission_finding_count` and the task-level subscore
fields used for the v0-candidate aggregate metrics. `control_replay_passed`
records whether the benchmark's task-level control replay behaved as expected,
which keeps secure-control backend behavior distinct from an agent's false
report. For vulnerable tasks, v0-candidate pass/fail uses control replay as an
integrity gate but does not award vulnerable-task score credit for
agent-independent control replay. `invalid_submission` tracks malformed or
missing submissions separately from false reports.

Adapter-level model parse errors are also separate from `invalid_submission`.
For example, the no-tools Kiro adapter records parse failures in
`model-output.json`; if it can still write a syntactically valid empty
`findings` list, the scorer treats the task as a normal no-finding miss rather
than a malformed submission. Use `invalid_submission` for missing or unscorable
submission files, and use adapter parse-error counters to audit model-output
quality.

For live tool-agent runs, the runner also summarizes optional ignored artifacts
when an adapter writes them beside `submission.json`:

- `model_tool_plan_artifact` and `model_tool_plan_artifact_count` record whether
  `model-tool-plan.json` was present and parseable.
- `tool_probe_artifact` and `per_task_tool_probe_artifact_count` record whether
  `tool-probes.json` was present and parseable.
- `executed_probe_count` and `executed_tool_probe_total` count executed probes.
  The runner accepts both the Kiro schema field `executed_probe_count` and the
  older heuristic schema field `probe_count`.
- `fallback_probe_count` and `fallback_probe_total` count safe fallback probes
  when the adapter reports them.
- `submission_finding_count` and `scored_submission_finding_total` are
  scorer-derived counts from the actual submission files.
- `submitted_finding_count` and `submitted_finding_total` are optional adapter
  telemetry from `tool-probes.json`, not scorer-validated vulnerability
  evidence. A no-tools run can therefore have a nonzero
  `scored_submission_finding_total` and a zero `submitted_finding_total`.
  Use scorer-derived counts and task pass/fail fields for benchmark scoring.
- `planner_returncode`, `planner_failure_count`, `planner_parse_error`, and
  `planner_parse_error_count` come from `model-tool-plan.json.metadata` when
  available. `planner_failure_count` counts nonzero planner return codes from
  parseable plan artifacts; use `planner_parse_error_count` for timeout or
  parse-error telemetry. Missing or malformed optional tool artifacts are
  ignored rather than making the task unscorable.

When present, each per-task summary record may include:

- `model_tool_plan_artifact`
- `tool_probe_artifact`
- `executed_probe_count`
- `fallback_probe_count`
- `submitted_finding_count`
- `planner_returncode`
- `planner_parse_error`

When `--target-log-dir` is supplied, each per-task summary record also includes:

- `target_request_count`
- optional `target_request_warning`, such as `target_log_missing` or
  `no_target_requests_correlated`

At the run level, `target_request_correlated_task_count` and
`target_request_coverage_rate` summarize how much of the run has target-side
request-log evidence. When no `--target-log-dir` is supplied, both values are
`null`.
