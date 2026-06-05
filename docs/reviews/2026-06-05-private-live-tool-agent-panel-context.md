# Private Live Tool-Agent Panel Context

Section: scorer, runner, request logs, live proof, and holdout anti-gaming.

AuthZBench-SaaS remains alpha/pre-v0. This slice adds protected private
holdout live/tool-agent execution with target-side request-log correlation.
It must not be treated as a finished leaderboard launch or final v0 release.

## Change Under Review

- `scripts/protected_private_eval.py` now accepts `--target-log-dir`.
- Protected private runs correlate target-side request logs by `run_id`,
  `task_id`, and `agent_id` after recording the relevant app-log offset before
  each task.
- The protected agent process still runs from a temporary empty workspace and
  receives rendered context only.
- Inherited `AUTHZBENCH_TARGET_LOG_DIR` and `AUTHZBENCH_REQUEST_LOG_DIR` are
  removed from the agent environment.
- Raw private result bundles can preserve `model-tool-plan.json`,
  `tool-probes.json`, and per-task `target-requests.jsonl`, but those remain
  ignored under `results/`.
- `scripts/kiro_live_tool_agent.py` now performs one clearly marked safe GET
  fallback probe if the planner returns no executable probes. Fallback-only
  evidence does not create a finding.

## Redacted Execution Evidence

Tracked redacted artifact:

- `docs/protected-private-live-kiro-sonnet-2026-06-05.redacted.json`

Aggregate metrics:

- 24 private-holdout tasks
- 12 vulnerable tasks
- 12 controls
- 6 denial controls
- 6 authorized-allow controls
- Kiro live tool-agent with `claude-sonnet-4.6`
- `harness_type`: `tool-agent`
- 24/24 model-tool-plan artifacts
- 24/24 per-task tool-probe artifacts
- 107 executed live probes
- 0 fallback safe GET probes in the committed-SHA run
- 24/24 target-request correlated tasks
- target-request coverage rate: 1.0
- zero control false reports
- zero invalid submissions
- 12 v0-passed controls
- zero exploit-proven vulnerable tasks
- raw private artifacts tracked: false
- tracked private manifests: 0

## Validation

Commands run after code changes:

```bash
python3 -Wd -m unittest discover -s tests -p 'test_kiro_live_tool_agent.py'
python3 -Wd -m unittest discover -s tests -p 'test_protected_private_eval.py'
python3 -m compileall -q scripts/kiro_live_tool_agent.py scripts/protected_private_eval.py tests/test_kiro_live_tool_agent.py tests/test_protected_private_eval.py
git diff --check
```

Private live execution used Docker Compose targets with request logging enabled,
then `docker compose down` was run after completion.

## Privacy Boundary

Tracked artifacts must not include private task IDs, private task paths, seeds,
route paths, refs, oracle bodies, prompt text, transcripts, raw Kiro output,
local result paths, raw request logs, or private filesystem details.

The tracked artifact is aggregate-only. Raw private artifacts remain ignored
under `results/` and target request logs remain ignored under `captures/`.

## Known Limitations

- This is one private live/tool-agent run, not multi-seed private scoring.
- The adapter supports one safe fallback probe after a planner parse failure,
  but the committed-SHA evidence run did not need fallback. Fallback-only
  evidence produces target-request evidence only and does not create a finding.
- The run proves private live correlation and protected execution, but it does
  not prove strong model performance on vulnerable tasks.
- This does not by itself complete holdout/anti-gaming or final release
  readiness.
