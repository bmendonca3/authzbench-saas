# Kiro Live Tool-Agent Baseline Panel Context

Section: baseline methodology and live-agent evidence.

AuthZBench-SaaS remains alpha/pre-v0. This slice adds a current public
tool-agent baseline, but it must not be treated as private-holdout or
leaderboard evidence.

## Change Under Review

- Added `scripts/kiro_live_tool_agent.py`.
- Added `tests/test_kiro_live_tool_agent.py`.
- Added `baselines/kiro-live-tool-agent-sonnet-current-public-44-summary.json`.
- Registered `kiro-live-tool-agent-sonnet-current-public-44` as
  `kind: tool_agent_baseline`.
- Hardened `scripts/validate_baseline_registry.py` so current public
  tool-agent baselines must report:
  - full target-request correlation
  - one model-tool plan artifact per public task
  - one tool-probe artifact per public task
  - planner parse/failure counts

## Adapter Behavior

The adapter:

1. Receives the normal rendered task context from `authzbench.run`.
2. Asks Kiro `claude-sonnet-4.6` to plan JSON HTTP probes from the task
   objective, policy, actors, refs, and API docs.
3. Executes model-planned probes against the live Docker target using
   AuthZBench request-correlation headers.
4. Writes per-task local artifacts:
   - `model-tool-plan.json`
   - `tool-probes.json`
   - `submission.json`
5. Submits a finding only when the referenced evidence probe was executed live,
   returned a status below 300, and returned a non-error response body.

Raw result bundles, request logs, Kiro stdout/stderr, transcripts, and panel
logs remain ignored and untracked.

## Committed-SHA Run Evidence

Adapter checkpoint commit:

- `ceae51599edcdc0d973d8424e13261100e4d6f7d`

Command:

```bash
python3 -m authzbench.run \
  --task 'tasks/*/*.json' \
  --agent-cmd 'python3 scripts/kiro_live_tool_agent.py --model claude-sonnet-4.6 --timeout-seconds 45 --max-probes 5' \
  --results-dir results/kiro-live-tool-agent-sonnet-current-public-committed \
  --timeout-seconds 75 \
  --benchmark-commit-sha "$(git rev-parse HEAD)" \
  --agent kiro_live_tool_agent \
  --model claude-sonnet-4.6 \
  --harness-type tool-agent \
  --target-log-dir captures/request-logs
```

Aggregate result:

- `task_count`: 44
- `passed_count`: 26
- `vulnerable_task_count`: 18
- `control_task_count`: 26
- `authorized_allow_control_task_count`: 10
- `exploit_proven_success_rate`: 0.7778
- `false_positive_rate`: 0.0
- `boundary_reasoning_pass_rate`: 0.0
- `target_request_correlated_task_count`: 44
- `target_request_coverage_rate`: 1.0
- `model_tool_plan_artifact_count`: 44
- `per_task_tool_probe_artifact_count`: 44
- `executed_tool_probe_total`: 100
- `planner_parse_error_count`: 0
- `planner_failure_count`: 0
- `zero_executed_task_count`: 0

## Public Claim Boundary

Acceptable public claim:

> Current public live HTTP tool-agent baseline exists for the public split, with
> Kiro-planned probes, per-task tool artifacts, and 44/44 target-request
> correlation.

Unacceptable public claims:

- v0 is ready
- leaderboard is ready
- private holdout proof exists
- the run is leaderboard eligible
- public tasks are enough for final model ranking

Remaining strict-v0 blockers include private holdouts, artifact-backed
leaderboard submissions, release evidence, protected leaderboard execution, and
final sectional review.
