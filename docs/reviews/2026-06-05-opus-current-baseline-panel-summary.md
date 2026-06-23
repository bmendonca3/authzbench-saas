# Opus Current Baseline Panel Summary

Date: 2026-06-05

Section: baseline methodology and leaderboard schema

Scope: two Kiro `claude-opus-4.6` no-tools runs on the current 44-task public
split.

## Reviewers Counted

- Gemini 3.5 Flash (High): verified Antigravity label; usable findings.
- Gemini 3.1 Pro (High): verified Antigravity label; usable findings.
- panel review: used as the panel reviewer for final synthesis.

Claude Sonnet 4.6 and Claude Opus 4.6 labels were verified in the panel logs,
but they produced no usable review text for this run, so they are not counted as
substantive reviewers.

## Findings

1. The two Opus summaries are valid repeated current public model-family
   evidence only because they are kept public-split, no-tools, and not
   leaderboard eligible.
2. The registry update is honest: it reaches five repeated current public
   no-tools model families, keeps `v0_baseline_ready: false`, and still reports
   the missing true tool-agent baseline.
3. The Opus metrics are accurately framed. Both runs passed 27 of 44 tasks,
   proved 12 of 18 vulnerable replays, kept zero false positives, and fully
   passed only 1 vulnerable task because boundary reasoning was `0.0556`.
4. The tracked Opus summaries omit raw task arrays, ignored result directories,
   stdout/stderr, captures, private holdouts, local filesystem paths, and
   personal information.
5. The panel found stale baseline-methodology wording in
   `docs/reviews/review-registry.json`.

## Disposition

Accepted and fixed. `docs/reviews/review-registry.json` now lists this summary
and says five repeated current public no-tools families exist, with a true
tool-agent baseline still missing.

This slice improves baseline breadth and satisfies the repeated public model
family count, but it does not change v0 readiness: the benchmark still needs a
true tool-agent baseline, private-holdout leaderboard execution, release
evidence, and final sectional review before any v0 or leaderboard-ready claim.
