# Haiku Current Baseline Panel Summary

Date: 2026-06-05

Section: baseline methodology and leaderboard schema

Scope: two Kiro `claude-haiku-4.5` no-tools runs on the current 44-task public
split.

## Reviewers Counted

- Gemini 3.5 Flash (High): verified Antigravity label; usable findings.
- Gemini 3.1 Pro (High): verified Antigravity label; usable findings.
- panel review: used as the panel reviewer for final synthesis
  because the session had already reached the live reviewer thread limit.

Claude Sonnet 4.6 and Claude Opus 4.6 labels were verified in the panel logs,
but they produced no usable review text for this run, so they are not counted as
substantive reviewers.

## Findings

1. The two Haiku summaries are valid repeated current public model-family
   evidence only because they are kept public-split, no-tools, and not
   leaderboard eligible.
2. The registry update is honest: it moves repeated current public families from
   three to four, keeps `v0_baseline_ready: false`, and still reports the
   missing fifth family plus the missing tool-agent baseline.
3. The Haiku metrics are accurately framed. Both runs passed 26 of 44 tasks,
   proved 4 of 18 vulnerable replays, kept zero false positives, and had zero
   full vulnerable-task passes because boundary reasoning was `0.0`.
4. The tracked Haiku summaries omit raw task arrays, ignored result directories,
   stdout/stderr, captures, private holdouts, local filesystem paths, and
   personal information.
5. The panel found stale count wording in `docs/launch-report.md` and
   `docs/reviews/review-registry.json`.

## Disposition

Accepted and fixed. `docs/launch-report.md` now says four repeated current
public no-tools baseline families. `docs/reviews/review-registry.json` now lists
this summary and says four repeated current public no-tools families exist, with
one more repeated family and a true tool-agent baseline still missing.

This slice improves baseline breadth but does not change v0 readiness: the
benchmark still needs one additional repeated current model/agent family, a true
tool-agent baseline, private-holdout leaderboard execution, release evidence,
and final sectional review before any v0 or leaderboard-ready claim.
