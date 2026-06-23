# DeepSeek Current Baseline Panel Summary

Date: 2026-06-05

Section: baseline methodology and leaderboard schema

Scope: two Kiro `deepseek-3.2` no-tools runs on the current 44-task public
split.

## Reviewers Counted

- Gemini 3.5 Flash (High): verified Antigravity label; usable findings.
- Gemini 3.1 Pro (High): verified Antigravity label; usable findings.
- panel review: used as the panel reviewer for final synthesis.

Claude Sonnet 4.6 and Claude Opus 4.6 labels were verified in the panel logs,
but they produced no usable review text for this run, so they are not counted as
substantive reviewers.

## Findings

1. The two DeepSeek summaries are useful evidence for one repeated current
   public model family, but only because the registry keeps them public-split,
   no-tools, and not leaderboard eligible.
2. The registry update avoids overclaiming: it marks the DeepSeek run as
   `model_baseline`, not `tool_agent_baseline`, and keeps
   `v0_baseline_ready: false`.
3. The docs clearly explain that DeepSeek was control-restrained: both runs
   passed all 26 controls, kept zero false positives, and proved no vulnerable
   exploits.
4. The review registry needed to be updated to include this summary and the new
   count of three repeated current public model families.

## Disposition

Accepted and fixed. This slice improves baseline credibility and moves the
baseline registry from two to three repeated current public model families, but
it does not change v0 readiness: the benchmark still needs two additional
repeated current model/agent families, a true tool-agent baseline,
private-holdout leaderboard execution, and release evidence before any v0 or
leaderboard-ready claim.
