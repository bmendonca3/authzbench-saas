# Sonnet Current Baseline Panel Context

Question: do the two new Kiro `claude-sonnet-4.6` no-tools runs improve
AuthZBench-SaaS baseline credibility without overclaiming v0, leaderboard, or
private-holdout readiness?

Files to review:

- `baselines/kiro-claude-sonnet-4.6-current-public-44-run1-summary.json`
- `baselines/kiro-claude-sonnet-4.6-current-public-44-run2-summary.json`
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
  --agent-cmd 'python3 scripts/kiro_baseline_agent.py --model claude-sonnet-4.6 --timeout-seconds 60' \
  --results-dir results/kiro-claude-sonnet-4.6-current-public \
  --timeout-seconds 75 \
  --benchmark-commit-sha "$(git rev-parse HEAD)" \
  --agent kiro_baseline_agent \
  --model claude-sonnet-4.6 \
  --harness-type no-tools-model
```

The command was run twice on commit
`aac3247cce447169e12bfaf1c5d60497f648d675`.

Run 1:

- run id: `20260605T155602281565Z-5b846714`
- task count: 44
- passed count: 29
- mean score: 0.8739
- v0 mean score: 0.6591
- invalid submissions: 0
- exploit-proven vulnerable tasks: 14 of 18
- vulnerable full-pass tasks: 3 of 18
- controls passed: 26 of 26
- control false reports: 0
- false-positive rate: 0.0

Run 2:

- run id: `20260605T155927462703Z-81ee0cbf`
- task count: 44
- passed count: 29
- mean score: 0.8739
- v0 mean score: 0.6591
- invalid submissions: 0
- exploit-proven vulnerable tasks: 14 of 18
- vulnerable full-pass tasks: 3 of 18
- controls passed: 26 of 26
- control false reports: 0
- false-positive rate: 0.0

Intended registry meaning:

- Add a second current public model family: `kiro-claude-sonnet`.
- Add a second repeated model baseline: `run_count: 2` with two distinct
  `run_artifacts`.
- Keep `leaderboard_eligible: false`.
- Keep `v0_baseline_ready: false` because three more repeated families and a
  true tool-agent baseline are still missing.

Current validator output:

- `baseline_count: 7`
- `current_public_model_family_count: 2`
- `repeated_model_baseline_count: 2`
- `has_current_public_tool_agent_baseline: false`
- `v0_baseline_ready: false`

Privacy/publication constraints:

- Full raw results remain ignored under `results/`.
- Tracked summary files must not include local result paths, prompt text, model
  stdout/stderr, private holdouts, captures, or personal information.
