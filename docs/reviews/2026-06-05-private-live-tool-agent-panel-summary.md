# Private Live Tool-Agent Panel Summary

Section: scorer, runner, request logs, live proof, and holdout anti-gaming.

Disposition: accepted for the alpha/pre-v0 private live/tool-agent execution
checkpoint.

The panel accepted the protected private live/tool-agent slice as evidence that
maintainers can run private holdouts with live HTTP tool-agent probing and
target-side request-log correlation without exposing private manifests or
target-log paths to the agent workspace. The tracked artifact is aggregate-only
and does not publish private task IDs, private task paths, seeds, route paths,
refs, oracle bodies, prompt text, transcripts, raw Kiro output, local result
paths, or raw request logs.

This does not make the whole benchmark v0-ready.

## Verified Reviewers

- Gemini 3.5 Flash (High): accepted and recommended making
  `scorer_runner_request_logs_live_proof` v0-ready. Verified propagated label in
  panel log.
- Gemini 3.1 Pro (High): accepted and recommended keeping
  `holdout_contamination_anti_gaming` blocked. Verified propagated label in
  panel log.
- Claude Sonnet 4.6 (Thinking): label verified, but the run produced an empty
  review output, so it is not counted for substantive findings.
- Claude Opus 4.6 (Thinking): label verified, but the run produced an empty
  review output, so it is not counted for substantive findings.
- panel reviewer: parent-review fallback.

Raw panel logs are intentionally untracked under `docs/reviews/panel-logs/`.

## Accepted Evidence

- Protected private live evaluator:
  - `scripts/protected_private_eval.py`
- Kiro live tool-agent adapter:
  - `scripts/kiro_live_tool_agent.py`
- Focused tests:
  - `tests/test_protected_private_eval.py`
  - `tests/test_kiro_live_tool_agent.py`
- Redacted private live execution artifact:
  - `docs/protected-private-live-kiro-sonnet-2026-06-05.redacted.json`

Current redacted execution evidence:

- benchmark commit SHA: `5d30f48c83ae43d9931b88c2de898ed4ea4e35f5`
- 24 private-holdout tasks
- 12 vulnerable tasks
- 12 controls
- 6 denial controls
- 6 authorized-allow controls
- Kiro live tool-agent with `claude-sonnet-4.6`
- 24/24 model-tool-plan artifacts
- 24/24 per-task tool-probe artifacts
- 107 executed live probes
- 0 fallback probes
- 24/24 target-request correlated tasks
- target-request coverage rate: 1.0
- zero control false reports
- zero invalid submissions
- zero exploit-proven vulnerable tasks
- 12 v0-passed controls
- agent workspace: temporary empty workspace
- agent input: rendered context only
- tracked private manifests: 0
- tracked raw private artifacts: false

## Findings And Disposition

1. High: protected private live/tool-agent execution with target-side request
   correlation is now demonstrated.
   Disposition: accepted. The evaluator records the app-log offset before each
   task, runs the agent from a temporary empty workspace, strips inherited
   target-log environment variables, and correlates target logs by `run_id`,
   `task_id`, and `agent_id`.

2. High: the redacted private live artifact preserves the private holdout
   boundary.
   Disposition: accepted. It contains aggregate metrics only and omits task
   rows, private identifiers, raw request logs, transcripts, prompts, and local
   raw result paths.

3. Medium: target-log buffering could cause a race if logs flush after the
   agent exits.
   Disposition: fixed. `scripts/protected_private_eval.py` now uses a short
   settle/retry window before declaring a task uncorrelated.

4. Low: fallback probes must not create findings.
   Disposition: accepted and tested. Fallback probes are GET-only, counted in
   `fallback_probe_count`, and cannot create findings because they are not tied
   to a model-planned `evidence_probe_id`.

5. Low: this is not strong private vulnerable-task model performance.
   Disposition: documented. The run proves protected private live execution and
   target correlation, not strong exploit success; exploit-proven vulnerable
   task count is zero.

## Section Readiness

`scorer_runner_request_logs_live_proof` can be marked v0-ready.

`holdout_contamination_anti_gaming` remains not v0-ready.

## Residual v0 Blockers

- Final task-mix review is still required.
- Multi-seed private holdout scoring is not complete.
- Final holdout anti-gaming review is still required.
- Final privacy/package/release-readiness review is still required.
