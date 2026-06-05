# Qwen Current Baseline Panel Context

Question: do the two new Kiro `qwen3-coder-next` no-tools runs improve
AuthZBench-SaaS baseline credibility without overclaiming v0, leaderboard, or
private-holdout readiness?

Files to review:

- `baselines/kiro-qwen3-coder-next-current-public-44-run1-summary.json`
- `baselines/kiro-qwen3-coder-next-current-public-44-run2-summary.json`
- `baselines/baseline-registry.json`
- `scripts/validate_baseline_registry.py`
- `tests/test_baseline_registry.py`
- `baselines/README.md`
- `docs/baseline-credibility.md`
- `docs/status.md`
- `docs/launch-report.md`

Actual commands run:

```bash
python3 -m authzbench.run \
  --task 'tasks/*/*.json' \
  --agent-cmd 'python3 scripts/kiro_baseline_agent.py --model qwen3-coder-next --timeout-seconds 60' \
  --results-dir results/kiro-qwen3-coder-next-current-public \
  --timeout-seconds 75 \
  --benchmark-commit-sha "$(git rev-parse HEAD)" \
  --agent kiro_baseline_agent \
  --model qwen3-coder-next \
  --harness-type no-tools-model
```

The command was run twice on commit
`ff6f0d2376188caa2159e146966002306f789ebf`.

Run 1:

- run id: `20260605T152209571409Z-402daf19`
- task count: 44
- passed count: 26
- mean score: 0.5977
- v0 mean score: 0.5909
- invalid submissions: 1
- exploit-proven vulnerable tasks: 0 of 18
- controls passed: 26 of 26
- control false reports: 0
- false-positive rate: 0.0
- model output parse errors: 13
- model command failures: 4

Run 2:

- run id: `20260605T153112429695Z-d6829fc5`
- task count: 44
- passed count: 25
- mean score: 0.5682
- v0 mean score: 0.5682
- invalid submissions: 1
- exploit-proven vulnerable tasks: 0 of 18
- controls passed: 25 of 26
- control false reports: 0
- false-positive rate: 0.0385
- model output parse errors: 11
- model command failures: 3

Intended registry meaning:

- Add one current public model family: `kiro-qwen`.
- Add one repeated model baseline: `run_count: 2` with two distinct
  `run_artifacts`.
- Keep `leaderboard_eligible: false`.
- Keep `v0_baseline_ready: false` because four more repeated families and a
  true tool-agent baseline are still missing.

Current validator output:

- `baseline_count: 6`
- `current_public_model_family_count: 1`
- `repeated_model_baseline_count: 1`
- `has_current_public_tool_agent_baseline: false`
- `v0_baseline_ready: false`

Privacy/publication constraints:

- Full raw results remain ignored under `results/`.
- Tracked summary files must not include local result paths, prompt text, model
  stdout/stderr, private holdouts, captures, or personal information.
