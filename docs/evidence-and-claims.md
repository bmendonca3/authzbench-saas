# Evidence And Claims

AuthZBench-SaaS should be easy to audit without overstating what the current
repo proves. Use this matrix when writing README text, release notes, benchmark
cards, LinkedIn posts, or external-review notes.

## Current Claim Matrix

| Evidence | What It Proves | What It Does Not Prove |
| --- | --- | --- |
| 46 public tasks across 6 synthetic SaaS apps | the public scaffold covers multiple SaaS authorization surfaces, including the first project-management multi-step workflow wave | public-split scores are private leaderboard scores |
| deterministic scorer replay | submitted evidence can be checked against backend behavior | the agent necessarily interacted with a live target unless request-log correlation is present |
| secure controls and authorized-allow controls | the benchmark can penalize false positives and over-reporting | all real SaaS false-positive patterns are covered |
| stale 44-task public model/tool-agent baselines | the harness has historical comparison artifacts and visible failure modes | current 46-task model rankings or leaderboard eligibility |
| target-side request logs | live target interaction can be observed and correlated when configured | target logs alone prove the exploit; replay remains authoritative |
| protected private-holdout summaries | maintainers have private release-candidate evidence without publishing holdout internals | public users can reproduce private scores from the repo |
| one eligible private-holdout leaderboard row | the submission validator can validate an artifact-backed private row | hosted public leaderboard readiness or broad model performance |
| strict maintainer release gate | current maintainer checkout satisfies the configured release-candidate gates | authorization to tag v0 or claim v1-scale external validation |

## Approved Public Framing

Use:

- `alpha/pre-v0 benchmark`
- `release-candidate evidence`
- `public-split baseline`
- `protected private-holdout evidence`
- `deterministic backend replay`
- `target-request correlation when live Docker targets are used`

Avoid:

- `hosted leaderboard-ready`
- `validated model benchmark`
- `finished v0`
- `production vulnerability discovery benchmark`
- `private holdouts are publicly reproducible`
- `public-split scores are final rankings`

## Headline Metrics

For release-facing summaries, prefer:

- `exploit_proven_success_rate`
- `false_positive_rate`
- `boundary_reasoning_pass_rate`
- `control_execution_pass_rate`
- `authorized_allow_pass_rate`
- `target_request_coverage_rate` for live-target runs
- `invalid_submission_rate`
- `v0_mean_score` as the compatibility aggregate

Do not rank agents by legacy `mean_score` alone.

## Generated Charts

The generated charts under
[`docs/assets/benchmark-charts/`](assets/benchmark-charts/) make the current
evidence easier to inspect:

![Public baseline metrics](assets/benchmark-charts/current-public-baselines.svg)

![Task mix](assets/benchmark-charts/task-mix.svg)

![Evidence readiness](assets/benchmark-charts/evidence-readiness.svg)

Regenerate them with:

```bash
python3 scripts/generate_benchmark_charts.py
```

These visuals summarize tracked public-safe artifacts only. They do not turn
public-split scores into private-holdout leaderboard rankings. Rows marked
stale need rerun before current comparison.
