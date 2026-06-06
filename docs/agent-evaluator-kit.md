# Agent Evaluator Kit

This page shows the smallest useful path for connecting an external agent to
AuthZBench-SaaS.

## Runner Contract

`python3 -m authzbench.run` renders each task into a `context.json` file and
expects the agent to write a `submission.json` file.

The runner sets:

- `AUTHZBENCH_CONTEXT`: rendered task context path
- `AUTHZBENCH_SUBMISSION`: output path for the agent submission
- `AUTHZBENCH_RUN_ID`: run identifier
- `AUTHZBENCH_TASK_ID`: task identifier
- `AUTHZBENCH_AGENT_ID`: agent identifier used for request-log correlation

Agent commands can also use `{context}` and `{submission}` placeholders.

## Minimal Template

[`examples/agents/minimal_no_findings_agent.py`](../examples/agents/minimal_no_findings_agent.py)
is intentionally simple. It reads the context and writes:

```json
{
  "findings": []
}
```

That is not a serious security agent. It is a wiring check: it should pass
secure controls and fail vulnerable tasks.

Run it on one secure control:

```bash
python3 -m authzbench.run \
  --task tasks/project_mgmt/pm_same_tenant_read_control.json \
  --agent-cmd 'python3 examples/agents/minimal_no_findings_agent.py' \
  --results-dir results/minimal-agent \
  --timeout-seconds 10 \
  --benchmark-commit-sha "$(git rev-parse HEAD)" \
  --agent minimal-no-findings \
  --model none \
  --harness-type template
```

Expected result: the secure-control task passes because no finding is reported.

Run it on a vulnerable task:

```bash
python3 -m authzbench.run \
  --task tasks/project_mgmt/pm_bola_read_alpha_from_beta.json \
  --agent-cmd 'python3 examples/agents/minimal_no_findings_agent.py' \
  --results-dir results/minimal-agent \
  --timeout-seconds 10 \
  --benchmark-commit-sha "$(git rev-parse HEAD)" \
  --agent minimal-no-findings \
  --model none \
  --harness-type template
```

Expected result: the vulnerable task fails because the agent did not submit
replayable exploit proof.

## Inspect Artifacts

After a run, inspect:

- `summary.json`
- `<task_id>/context.json`
- `<task_id>/submission.json`
- `<task_id>/score.json`
- `<task_id>/transcript.json`
- `<task_id>/target-requests.jsonl` when live target logging is enabled

Use `score.json` for task-level pass/fail and `summary.json` for aggregate
metrics. Use `transcript.json` to see scorer-owned replay evidence.
