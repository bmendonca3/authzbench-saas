# Baseline Variance Analysis

Status: scaffold from existing repeated baseline evidence.

The current public split has repeated runs for four no-tools model families and
one live HTTP tool-agent family. This file records the variance questions that
must be answered before the benchmark is described as research-grade.

## Current Evidence

- Qwen current public 46-task no-tools runs: 2 runs.
- Claude Haiku current public 46-task no-tools runs: 2 runs.
- Claude Sonnet current public 46-task no-tools runs: 2 runs.
- GLM current public 46-task no-tools runs: 2 runs.
- Claude Sonnet current public 46-task live HTTP tool-agent runs: 2 runs.

## Metrics To Analyze

- `v0_mean_score`
- `exploit_proven_success_rate`
- `vulnerable_full_pass_count`
- `boundary_reasoning_pass_rate`
- `false_positive_rate`
- `authorized_allow_pass_rate`
- `invalid_submission_rate`
- `target_request_coverage_rate` for live HTTP runs

## Initial Interpretation

The repeated runs are enough to show that variance exists, but not enough to
make a mature statistical claim. The most important current signal is
qualitative: exploit replay sometimes succeeds while boundary reasoning remains
weak across current public model/tool-agent runs.

## Required Next Work

- Generate a variance table directly from baseline summaries.
- Add confidence intervals or another clearly documented uncertainty estimate
  only when the run count supports it.
- Separate public-split diagnostic variance from private-holdout leaderboard
  evidence.
- Recompute this file after any task-count or scoring-contract change.
