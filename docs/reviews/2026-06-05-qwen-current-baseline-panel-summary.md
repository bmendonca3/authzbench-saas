# Qwen Current Baseline Panel Summary

Date: 2026-06-05

Section: baseline methodology and leaderboard schema

Scope: two Kiro `qwen3-coder-next` no-tools runs on the current 44-task public
split.

## Reviewers Counted

- Gemini 3.5 Flash (High): verified Antigravity label; usable findings.
- Gemini 3.1 Pro (High): verified Antigravity label; usable findings.
- Parent ChatGPT review: used as the ChatGPT reviewer for final synthesis.

Claude Sonnet 4.6 and Claude Opus 4.6 labels were verified in the panel logs,
but they produced no usable review text for this run, so they are not counted as
substantive reviewers.

## Findings

1. The two Qwen summaries are useful evidence for one repeated current public
   model family, but only because the registry keeps them public-split,
   no-tools, and not leaderboard eligible.
2. The README omitted the new current Qwen rows and still showed the older
   Qwen command shape. The README now uses the actual current run command and
   lists both current Qwen runs separately from legacy snapshots.
3. The registry validator originally treated repeated evidence mostly as "two
   files with distinct run IDs." It now validates each run artifact against the
   registry's expected harness type, agent, model, task count, and current public
   split counts.
4. `docs/status.md` misstated run 2's authorized-allow pass rate as `0.9`; the
   source summary reports `1.0`, and the table has been corrected.
5. `docs/baseline-credibility.md` was ambiguous about control false reports.
   It now states that both Qwen runs had zero control false-report findings,
   while run 2 still had one failed denial-control score and neither run proved
   vulnerable exploits.

## Disposition

Accepted and fixed. This slice improves baseline credibility but does not change
v0 readiness: the benchmark still needs four additional repeated current
model/agent families, a true tool-agent baseline, private-holdout leaderboard
execution, and release evidence before any v0 or leaderboard-ready claim.
