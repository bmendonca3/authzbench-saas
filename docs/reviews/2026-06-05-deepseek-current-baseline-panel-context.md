# DeepSeek Current Baseline Panel Context

Question: do the two new Kiro `deepseek-3.2` no-tools runs improve
AuthZBench-SaaS baseline credibility without overclaiming v0, leaderboard, or
private-holdout readiness?

Files to review:

- `baselines/kiro-deepseek-3.2-current-public-44-run1-summary.json`
- `baselines/kiro-deepseek-3.2-current-public-44-run2-summary.json`
- `baselines/baseline-registry.json`
- `scripts/validate_baseline_registry.py`
- `tests/test_baseline_registry.py`
- `baselines/README.md`
- `docs/baseline-credibility.md`
- `docs/status.md`
- `docs/launch-report.md`
- `README.md`

Actual command run:

```bash
python3 -m authzbench.run \
  --task 'tasks/*/*.json' \
  --agent-cmd 'python3 scripts/kiro_baseline_agent.py --model deepseek-3.2 --timeout-seconds 60' \
  --results-dir results/kiro-deepseek-3.2-current-public \
  --timeout-seconds 75 \
  --benchmark-commit-sha "$(git rev-parse HEAD)" \
  --agent kiro_baseline_agent \
  --model deepseek-3.2 \
  --harness-type no-tools-model
```

The command was run twice on commit
`73c8ea765b315f4f62052908ccf2ec0a7cc5770d`.

Run 1:

- run id: `20260605T161106535232Z-ba93e7b8`
- task count: 44
- passed count: 26
- mean score: 0.5977
- v0 mean score: 0.5909
- invalid submissions: 0
- exploit-proven vulnerable tasks: 0 of 18
- vulnerable full-pass tasks: 0 of 18
- controls passed: 26 of 26
- control false reports: 0
- false-positive rate: 0.0

Run 2:

- run id: `20260605T161728342040Z-d19ef2ac`
- task count: 44
- passed count: 26
- mean score: 0.5909
- v0 mean score: 0.5909
- invalid submissions: 0
- exploit-proven vulnerable tasks: 0 of 18
- vulnerable full-pass tasks: 0 of 18
- controls passed: 26 of 26
- control false reports: 0
- false-positive rate: 0.0

Intended registry meaning:

- Add a third current public model family: `kiro-deepseek`.
- Add a third repeated model baseline: `run_count: 2` with two distinct
  `run_artifacts`.
- Keep `leaderboard_eligible: false`.
- Keep `v0_baseline_ready: false` because two more repeated families and a
  true tool-agent baseline are still missing.

Current validator output:

- `baseline_count: 8`
- `current_public_model_family_count: 3`
- `repeated_model_baseline_count: 3`
- `has_current_public_tool_agent_baseline: false`
- `v0_baseline_ready: false`

Privacy/publication constraints:

- Full raw results remain ignored under `results/`.
- Tracked summary files must not include local result paths, prompt text, model
  stdout/stderr, private holdouts, captures, or personal information.
