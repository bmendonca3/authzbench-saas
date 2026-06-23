# Sonnet Current Baseline Panel Summary

Date: 2026-06-05

Section: baseline methodology and leaderboard schema

Scope: two Kiro `claude-sonnet-4.6` no-tools runs on the current 44-task public
split.

## Reviewers Counted

- Gemini 3.5 Flash (High): verified panel runner label; usable findings.
- Gemini 3.1 Pro (High): verified panel runner label; usable findings.
- panel review: used as the panel reviewer for final synthesis.

Claude Sonnet 4.6 and Claude Opus 4.6 labels were verified in the panel logs,
but they produced no usable review text for this run, so they are not counted as
substantive reviewers.

## Findings

1. The two Sonnet summaries are useful evidence for one repeated current public
   model family, but only because the registry keeps them public-split,
   no-tools, and not leaderboard eligible.
2. The registry update avoids overclaiming: it marks the Sonnet run as
   `model_baseline`, not `tool_agent_baseline`, and keeps
   `v0_baseline_ready: false`.
3. The docs initially highlighted Sonnet's 14 of 18 exploit-proven replays and
   zero control false positives without explaining the weak boundary reasoning
   that limited full vulnerable-task passes. The baseline tables and prose now
   expose boundary reasoning separately.
4. The panel warned that untracked summaries are not covered by the Git-tracked
   public validation privacy scan until staged or committed. The release path
   therefore includes an explicit staged-diff privacy scan before commit.

## Disposition

Accepted and fixed. This slice improves baseline credibility and moves the
baseline registry from one to two repeated current public model families, but it
does not change v0 readiness: the benchmark still needs three additional
repeated current model/agent families, a true tool-agent baseline,
private-holdout leaderboard execution, and release evidence before any v0 or
leaderboard-ready claim.
