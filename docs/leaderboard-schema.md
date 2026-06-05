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
| `exploit_proven_success_rate` | Vulnerable tasks with backend-replayed proof |
| `control_false_report_rate` | Secure-control tasks where the agent reported a finding |
| `control_execution_pass_rate` | Secure-control requests that behaved as expected |
| `authorized_allow_pass_rate` | Authorized-allow controls where permitted access succeeded |
| `false_positive_rate` | Compatibility alias for secure-control failures in alpha summaries |
| `boundary_reasoning_pass_rate` | Vulnerable tasks where the submitted actor/tenant/role boundary matched the oracle |
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
3. highest `mean_score`
4. lowest median runtime

This avoids both failure modes: over-reporting every sensitive route and saying
nothing on every task.

## Submission Requirements

A leaderboard submission should include:

- `summary.json`
- per-task `score.json`
- per-task `submission.json`
- per-task `agent.json`
- agent/model metadata
- benchmark version and commit SHA
