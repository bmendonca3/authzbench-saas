# Panel Review Prompt: Tool-Agent Baseline

Review only the tool-agent baseline slice described in:

`docs/reviews/2026-06-05-tool-agent-baseline-panel-context.md`

Focus on:

1. Whether `scripts/heuristic_tool_agent.py` is honestly a live HTTP
   tool-agent baseline rather than another deterministic oracle/scripted
   baseline.
2. Whether per-task artifacts and target-request correlation are strong enough
   to register it as a current public tool-agent baseline.
3. Whether the proposed registry/docs language avoids overclaiming v0,
   leaderboard readiness, private-holdout proof, or model capability.
4. Any concrete code/test/doc changes needed before committing this checkpoint.

Return concise findings with severity, evidence, and exact fixes. Do not edit
files, mutate git, install packages, or take external actions.
