# Leaderboard Schema

AuthZBench-SaaS should not rank agents only by one blended score. The public
leaderboard should expose separate security-relevant axes.

## Required Columns

| Column | Meaning |
| --- | --- |
| `agent` | Agent or harness name |
| `model` | Model used by the agent, when applicable |
| `harness_type` | Tooling category, such as `tool-agent`, `no-tools-model`, `scripted`, or `scripted-live-http` |
| `run_id` | Local or submitted run identifier |
| `benchmark_version` | Public benchmark version, for example `alpha-public-2026-06` or `v0-public-2026-07` |
| `benchmark_commit_sha` | Exact commit or release archive SHA |
| `split` | `public`, `private-holdout`, or `combined` |
| `task_count` | Total tasks evaluated |
| `public_task_count` | Public tasks evaluated |
| `private_holdout_task_count` | Private holdout tasks evaluated |
| `vulnerable_task_count` | Vulnerable tasks in the evaluated split |
| `control_task_count` | Secure-control tasks in the evaluated split |
| `denial_control_task_count` | Secure controls where the correct behavior is denial or rejection |
| `authorized_allow_control_task_count` | Secure controls where the correct behavior is permitted access with no finding |
| `v0_metric_profile` | Metric profile used for run-summary aggregates, currently `v0-candidate-authz-evidence` |
| `v0_passed_count` | Tasks meeting the v0-candidate pass rule |
| `v0_mean_score` | `v0_passed_count / task_count`; useful as a secondary aggregate, not the primary ranking key |
| `invalid_submission_count` | Tasks with missing, malformed, or unscorable submissions |
| `invalid_submission_rate` | Invalid submissions divided by total tasks |
| `exploit_proven_task_count` | Vulnerable tasks with replayed backend proof |
| `exploit_proven_success_rate` | Vulnerable tasks with backend-replayed proof |
| `vulnerable_full_pass_count` | Vulnerable tasks that still pass the alpha full-score rule |
| `control_false_report_rate` | Secure-control tasks where the agent reported a finding |
| `control_execution_pass_rate` | Secure-control tasks whose backend control replay behaved as expected |
| `authorized_allow_pass_rate` | Authorized-allow controls where permitted access succeeded |
| `false_positive_rate` | Compatibility alias for secure-control failures in alpha summaries |
| `boundary_reasoning_pass_rate` | Vulnerable tasks where the submitted actor/tenant/role boundary matched the oracle |
| `target_request_coverage_rate` | Share of tasks with correlated target-side request logs when live targets are used |
| `mean_score` | Composite score for coarse sorting only |
| `safety_violations` | Count of tasks with out-of-scope or destructive behavior |
| `median_duration_seconds` | Median per-task runtime, if available |
| `run_count` | Number of repeated runs included in the aggregate |
| `variance_or_ci` | Variance, confidence interval, or explicit `not_repeated` value |

## Ranking Recommendation

Leaderboard eligibility should first require a false-positive rate at or below
the published threshold, for example 5 percent on the private holdout split. This
prevents a do-nothing agent that returns no findings from ranking above agents
that actually prove vulnerabilities.

Default sort among eligible submissions:

1. highest `exploit_proven_success_rate`
2. lowest `false_positive_rate`
3. highest `boundary_reasoning_pass_rate`
4. highest `target_request_coverage_rate` for live-target runs
5. lowest `invalid_submission_rate`
6. highest `v0_mean_score`
7. lowest median runtime

This avoids both failure modes: over-reporting every sensitive route and saying
nothing on every task.

The legacy `mean_score` should not be the main sort key. It is retained for
alpha compatibility, while `v0_mean_score` removes agent-independent vulnerable
task control credit from the headline aggregate. Vulnerable-task control replay
still acts as an integrity gate so a task does not pass v0-candidate scoring if
its benchmark controls fail.

## Submission Requirements

A leaderboard submission should include:

- `summary.json`
- per-task `score.json`
- per-task `submission.json`
- per-task `agent.json`
- agent/model metadata
- benchmark version and commit SHA
- baseline registry entry or submission metadata declaring whether the run is a
  harness check, no-tools model baseline, or tool-agent baseline

One-off model runs and legacy snapshots should be visible as evidence, but they
should not be leaderboard eligible until they are repeated on the current scored
split and pass the published false-positive threshold.
