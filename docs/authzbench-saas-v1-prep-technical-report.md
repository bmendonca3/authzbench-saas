# AuthZBench-SaaS v1-Prep Technical Report Draft

Status: current-main v1-prep draft. This document describes the active
post-v0 development state while preserving the frozen v0.0 claim boundary.

## Claim Boundary

AuthZBench-SaaS v0.0 is the released historical artifact. Current `main` is now
post-v0 active development. It contains the first v1 task-expansion slice and a
49-task public split, but it is not a v1 release, a hosted leaderboard, or a
community-scale benchmark.

The frozen v0.0 evidence remains auditable at the 46-task release boundary. The
46-task model and tool-agent baselines are stale for current 49-task comparison
until rerun. They should be cited as frozen v0.0 diagnostics, not current v1
rankings.

## Current Public Split

The current v1-prep public split contains:

- 6 synthetic SaaS target families
- 49 public tasks
- 20 vulnerable tasks
- 29 secure controls
- 17 denial controls
- 12 authorized-allow controls

The first expansion slice adds billing entitlement coverage. The vulnerable
task checks whether a same-organization non-admin member can enable an
admin-only audit-export entitlement through the insecure route. The paired
controls check secure member denial, cross-organization denial, and authorized
admin allow behavior.

## Current Evidence

The current 49-task scripted sanity baseline passes all public tasks. It proves
that the expanded manifests, scorer, scripted oracle path, and baseline registry
agree. It does not prove model capability, leaderboard eligibility,
private-holdout performance, or v1 readiness.

The current 49-task public split also has repeated diagnostic Kiro baselines:
five no-tools model families and one live HTTP `claude-sonnet-4.6` tool-agent
family. The tool-agent pair preserves one model-plan artifact and one tool-probe
artifact per task, correlates target-side requests for all 49 tasks in both runs,
and reports zero planner or parser failures. These are public-split comparison
artifacts, not private-holdout rankings or hosted leaderboard rows.

The current registry separates:

- `current_public_harness_check` for deterministic current-split sanity checks
- `current_public_stale` for formerly current rows that need rerun before live
  comparison
- `legacy_snapshot` for older historical rows
- `release_snapshots` for frozen tagged-release evidence such as v0.0

Rows marked `requires_rerun_before_current_comparison` cannot support current
49-task comparison. That marker does not imply the frozen v0.0 release snapshot
itself needs to be rerun.

## Frozen v0.0 Evidence

The frozen v0.0 public split contained 46 public tasks: 19 vulnerable tasks, 27
secure controls, 16 denial controls, and 11 authorized-allow controls. Its
public baselines include four repeated no-tools model-family rows and one
repeated live HTTP tool-agent family. These are useful diagnostics for exploit
replay, false positives, request correlation, and weak boundary reasoning, but
they are stale for current 49-task comparison.

The v0.0 report remains in
[`authzbench-saas-v0.0-technical-report.md`](authzbench-saas-v0.0-technical-report.md).
Use it when describing the tagged release snapshot. Use this v1-prep report
when describing current `main`.

## Next Work

Before a v1 release, expand task volume, add rotating private holdouts, complete
boundary-reasoning calibration and external reviewer calibration, define hosted
or fully containerized submission governance, and keep chart/table captions
explicit about current versus stale evidence. After any v1 task or scoring
change, rerun current public no-tools and tool-agent baselines before making new
comparisons.
