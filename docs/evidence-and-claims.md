# Evidence And Claims

AuthZBench-SaaS should be easy to audit without overstating what the current
repo proves. Use this matrix when writing README text, release notes, benchmark
cards, LinkedIn posts, or external-review notes.

## Current Claim Matrix

| Evidence | What It Proves | What It Does Not Prove |
| --- | --- | --- |
| v0.0 release snapshot: 46 public tasks across 6 synthetic SaaS apps | the v0.0 public scaffold covers multiple SaaS authorization surfaces, including the first project-management multi-step workflow wave | that future expanded public splits have comparable current baselines before rerun |
| v1-prep public split: 49 public tasks across 6 synthetic SaaS apps | the first billing entitlement expansion slice is present in public manifests and controls | v1 release readiness, current v1 model comparisons, or hosted leaderboard operation |
| deterministic scorer replay | submitted evidence can be checked against backend behavior | the agent necessarily interacted with a live target unless request-log correlation is present |
| secure controls and authorized-allow controls | the benchmark can penalize false positives and over-reporting | all real SaaS false-positive patterns are covered |
| five repeated v0.0 46-task public model/agent families | four no-tools model families plus one live HTTP tool-agent family have v0.0 public-split replay evidence | broad model rankings, private-holdout performance, v1 comparability after task expansion, or leaderboard eligibility |
| two v0.0 46-task public live HTTP tool-agent runs | the tool-agent harness can repeatedly emit per-task plan/probe artifacts and target-request correlation on the v0.0 public split | private-holdout tool-agent performance, v1 comparability after task expansion, or hosted leaderboard readiness |
| stale public model/tool-agent baselines | the harness has historical comparison artifacts and visible failure modes | current model rankings or leaderboard eligibility |
| target-side request logs | live target interaction can be observed and correlated when configured | target logs alone prove the exploit; replay remains authoritative |
| historical workspace-separated private summaries | maintainers exercised rendered-context-only evaluation without publishing holdout internals | host-level isolation or current leaderboard eligibility |
| one historical private-holdout leaderboard row | the stable schema can validate its redacted source and repeated-run provenance | current eligibility, because its fingerprint was reconstructed after execution |
| one host-isolated private no-tools leaderboard-candidate row | the stable schema validates runner-emitted fingerprint provenance and release-candidate eligibility | hosted leaderboard operation, broad private model rankings, or private tool-agent eligibility |
| strict maintainer release gate | the maintainer checkout can report exact pass/fail v0 gates while keeping private holdouts out of public Git history | hosted leaderboard readiness or v1-scale external validation |
| v1 readiness checklist | v1 task expansion has a documented startup gate, stale-baseline policy, validation commands, and rerun matrix | v1 release readiness, new current model comparisons, or hosted leaderboard operation |

## Approved Public Framing

Use:

- `released v0.0 benchmark artifact`
- `v0.0 release evidence`
- `v0.0 release snapshot`
- `v1-prep branch`
- `v1 readiness checklist`
- `public-split baseline`
- `protected private-holdout evidence`
- `deterministic backend replay`
- `target-request correlation when live Docker targets are used`

Avoid:

- `hosted leaderboard-ready`
- `validated model benchmark`
- `v1/community-scale benchmark`
- `v1 release-ready`
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

![Model pass rate](assets/benchmark-charts/model-pass-rate.svg)

![Exploit-proven success](assets/benchmark-charts/exploit-proven-success.svg)

![False-positive rate](assets/benchmark-charts/false-positive-rate.svg)

![Boundary reasoning](assets/benchmark-charts/boundary-reasoning.svg)

![Task mix](assets/benchmark-charts/task-mix.svg)

![Evidence readiness](assets/benchmark-charts/evidence-readiness.svg)

Regenerate them with:

```bash
python3 scripts/generate_benchmark_charts.py
```

These visuals summarize tracked public-safe artifacts only. They do not turn
public-split scores into private-holdout leaderboard rankings. Rows marked
stale need rerun before current comparison.
