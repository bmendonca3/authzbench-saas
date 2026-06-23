# Tool-Agent Baseline Panel Summary

Section: baseline methodology and live-target proof.

## Reviewer Coverage

Counted reviewers:

- Gemini 3.1 Pro (High), verified in Antigravity log
- panel review

Partial or uncounted reviewers:

- Gemini 3.5 Flash (High): model label verified, but the run timed out before a
  final concise finding set
- Claude Sonnet 4.6 (Thinking): model label verified, no usable final output
- Claude Opus 4.6 (Thinking): model label verified, no usable final output

Raw panel logs are intentionally ignored under `docs/reviews/panel-logs/`.

## Decision

The heuristic live HTTP prober is useful, but it must not be counted as the v0
tool-agent baseline.

Accepted disposition:

- Register it, if at all, as a `harness_check` with
  `release_suitability: current_public_harness_check`.
- Use it to document stronger live-target request coverage across vulnerable
  and control tasks.
- Do not use it to satisfy `has_current_public_tool_agent_baseline: true`.
- Keep it non-leaderboard-eligible and not repeated-model evidence.

## Findings

1. High: the first proposed classification overclaimed tool-agent credibility.

   Evidence: `scripts/heuristic_tool_agent.py` uses deterministic phrase and
   objective matching for control detection, claim generation, and route
   selection. That makes it a stronger live harness check, not an autonomous
   model/tool-agent baseline.

   Disposition: accepted. The registry/docs must not classify this as
   `tool_agent_baseline`.

2. Positive: the run meaningfully improves live-target proof.

   Evidence from run `20260605T150659538894Z-d35d8376`:

   - 44 public tasks executed
   - 33 passed
   - 11 of 18 vulnerable tasks had exploit-proven credit
   - 26 control tasks had zero false reports
   - target request correlation covered 44 of 44 tasks
   - every task produced `tool-probes.json`

   Disposition: accepted. This is worth tracking as a current public live HTTP
   harness check once rerun from a committed benchmark state.

## Required Follow-Up

- Commit the heuristic prober and tests first.
- Rerun the live HTTP harness from the committed SHA.
- Add only the curated public-safe summary under `baselines/`.
- Update the registry as `harness_check`, not `tool_agent_baseline`.
- Leave v0 baseline readiness false until real repeated model/tool-agent
  baselines exist.
