# Current Public Tool-Agent Baseline Panel Summary

Date: 2026-06-06

Scope: current 46-task public live HTTP Kiro `claude-sonnet-4.6` tool-agent
baseline summary, baseline-registry entry, chart regeneration, and related
README/docs wording.

## Counted Reviewers

- Gemini 3.5 Flash (High), verified by Antigravity CLI log
- Gemini 3.1 Pro (High), verified by Antigravity CLI log
- Kiro CLI `claude-opus-4.8`, verified against the live Kiro model catalog
- ChatGPT subagent reviewer
- Parent ChatGPT synthesis

Claude Sonnet 4.6 and Claude Opus 4.6 Antigravity labels propagated in logs but
did not return substantive review output, so they are not counted.

Raw prompts and logs are kept under ignored `docs/reviews/panel-logs/` and are
not part of the public release artifact.

## Findings And Fixes

Reviewers agreed the new summary honestly satisfies the current-public
tool-agent registry gate:

- `release_suitability: current_public_split`
- `leaderboard_eligible: false`
- `run_count: 2`
- 46 of 46 tasks with `model-tool-plan.json`
- 46 of 46 tasks with `tool-probes.json`
- 46 of 46 tasks with target-request correlation
- no planner failures or parse errors

Accepted fixes before commit:

- clarified that the run is public-split evidence only, not private-holdout or
  leaderboard evidence
- clarified that the run fully passed zero vulnerable tasks because vulnerable
  boundary reasoning remained `0.0`
- updated README and baseline-credibility docs after a second current-public
  run so the tool-agent baseline is present and repeated
- tightened evidence-readiness chart wording so the repeated-model-family row
  counts repeated current model baselines, not one-off current tool-agent rows
- regenerated charts and chart data from the updated registry

## Claim Boundary

Supported claim:

`AuthZBench-SaaS now has two current 46-task public live HTTP tool-agent runs
with per-task plan/probe artifacts and full target-request correlation.`

Unsupported claims:

- private-holdout leaderboard readiness
- v0 baseline readiness
- fully solved vulnerable workflow tasks; vulnerable full-pass count is `0`
- hosted leaderboard readiness

## Verification

Parent-verified before commit:

- `docker info --format '{{.ServerVersion}}'`
- `docker compose up --build -d`
- `python3 scripts/container_smoke.py`
- `python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/kiro_live_tool_agent.py --model claude-sonnet-4.6 --timeout-seconds 45 --max-probes 5' --results-dir results/kiro-live-tool-agent-sonnet-current-public-46 --timeout-seconds 75 --benchmark-commit-sha "$(git rev-parse HEAD)" --agent kiro_live_tool_agent --model claude-sonnet-4.6 --harness-type tool-agent --target-log-dir captures/request-logs`
- repeated with `--results-dir results/kiro-live-tool-agent-sonnet-current-public-46-run2`
- `docker compose down`
- `python3 scripts/validate_baseline_registry.py`

Additional full validation is recorded in the commit verification output for
this checkpoint.
