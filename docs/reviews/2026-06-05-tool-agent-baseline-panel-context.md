# Tool-Agent Baseline Panel Context

Question: does the new heuristic live HTTP tool-agent baseline improve
AuthZBench-SaaS baseline credibility without overclaiming v0, leaderboard, or
model capability?

Files to review:

- `scripts/heuristic_tool_agent.py`
- `tests/test_heuristic_tool_agent.py`
- `authzbench/run.py`
- `scripts/validate_baseline_registry.py`
- `baselines/baseline-registry.json`
- `baselines/README.md`
- `docs/baseline-credibility.md`
- `docs/status.md`

Current implementation:

- Adds `scripts/heuristic_tool_agent.py`, a non-LLM live HTTP probing agent.
- The agent receives only runner context: public policy, objective, actors,
  refs, target URL, seed, and public API docs.
- The agent probes documented live routes using task-scoped request headers:
  `x-authzbench-run-id`, `x-authzbench-agent-id`, and `x-authzbench-task-id`.
- The agent writes:
  - `submission.json` for scoring
  - `tool-probes.json` per task with the live probes it attempted
- It submits no findings for control-worded tasks.
- It ranks successful live probes using public objective/API-doc relevance.
- It does not read task manifests, oracles, controls, private holdouts, or
  result artifacts.

Observed live run against the 44 public tasks:

- command:
  `python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/heuristic_tool_agent.py' --results-dir results/heuristic-tool-agent --timeout-seconds 20 --benchmark-commit-sha "$(git rev-parse HEAD)" --agent heuristic_tool_agent --model heuristic-http-prober-v1 --harness-type tool-agent --target-log-dir captures/request-logs`
- run id: `20260605T150659538894Z-d35d8376`
- task count: 44
- passed count: 33
- mean score: 0.8943
- v0 passed count: 33
- vulnerable task count: 18
- exploit-proven task count: 11
- control task count: 26
- control false report count: 0
- false-positive rate: 0.0
- target request correlated task count: 44
- target request coverage rate: 1.0
- per-task `tool-probes.json` files: 44

Intended claim:

- This is a current public-split tool-agent baseline and a useful non-LLM
  contrast.
- It is not a model baseline, not repeated, not private-holdout evidence, and
  not leaderboard eligible.
- It should satisfy the registry's
  `has_current_public_tool_agent_baseline: true` field only after a curated
  tracked summary is added.

Known remaining v0 gaps:

- five repeated current model/agent families are still missing
- private-holdout leaderboard submissions are still missing
- final release evidence fields remain false until exact checks pass
- final sectional review cannot be marked v0-ready yet
