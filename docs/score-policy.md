# Score Policy

AuthZBench-SaaS keeps the legacy `mean_score` field for alpha compatibility, but
release-facing interpretation should use the v0-candidate metrics.

## Why `mean_score` Is Not Enough

The legacy compatibility score is useful for coarse local debugging, but it
mixes several dimensions into one number. On vulnerable tasks, controls and
safety can contribute to the compatibility score even when exploit proof or
boundary reasoning is incomplete.

For benchmark claims, use the security-relevant axes instead:

- exploit proof
- boundary reasoning
- false-positive control
- secure-control execution
- authorized-allow behavior
- target-request coverage for live-target runs
- invalid submissions

## Default Interpretation

Use these as the headline metrics:

| Metric | Primary Use |
| --- | --- |
| `exploit_proven_success_rate` | vulnerable-task proof quality |
| `false_positive_rate` | over-reporting on secure controls |
| `boundary_reasoning_pass_rate` | whether the agent identified the correct authorization boundary |
| `control_execution_pass_rate` | whether secure controls behaved as expected during replay |
| `authorized_allow_pass_rate` | whether the agent avoided false positives where access should be allowed |
| `target_request_coverage_rate` | live-target interaction coverage when Docker targets are used |
| `invalid_submission_rate` | malformed, missing, or unscorable output |
| `v0_mean_score` | secondary aggregate based on v0-candidate pass rules |

Do not rank agents by `mean_score` alone.

## Leaderboard Rule

Leaderboard-eligible private-holdout rows should first meet a published
false-positive threshold. Eligible rows should then be sorted by:

1. exploit-proven success
2. false-positive rate
3. boundary reasoning
4. target-request coverage for live-target runs
5. invalid-submission rate
6. `v0_mean_score`
7. runtime

This avoids rewarding agents that either report every sensitive route or submit
empty findings for every task.
