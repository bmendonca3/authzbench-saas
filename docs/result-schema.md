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
```

## `context.json`

Rendered task context given to the agent:

- `task_id`
- `app`
- `seed`
- `policy`
- `objective`
- `allowed_hosts`
- `actors`
- `refs`
- `api_docs`
- `output_schema`

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

## `transcript.json`

Scorer-owned backend replay transcript. Each entry has:

- `name`: `proof` or the control name
- `request`: actor, method, path, and optional body
- `response`: status and JSON body returned by the benchmark app logic

## `summary.json`

Run-level aggregate:

- `run_id`
- `agent_cmd`
- `timeout_seconds`
- `task_count`
- `passed_count`
- `mean_score`
- `vulnerable_task_count`
- `control_task_count`
- `exploit_proven_success_rate`
- `false_positive_rate`
- per-task score records
