# AuthZBench-SaaS v1-Prep Technical Report Draft

Status: current-main v1-prep draft. This document describes the active
post-v0 development state while preserving the frozen v0.0 claim boundary.

## Claim Boundary

AuthZBench-SaaS v0.0 is the released historical artifact. Current `main` is now
post-v0 active development. It contains two v1 task-expansion slices and a
54-task public split, but it is not a v1 release, a hosted leaderboard, or a
community-scale benchmark.

The frozen v0.0 evidence remains auditable at the 46-task release boundary. The
46-task release baselines and 49-task v1-prep model/tool-agent baselines are
stale for current 54-task comparison. They should be cited as historical
diagnostics, not current v1 rankings.

## Current Public Split

The current v1-prep public split contains:

- 6 synthetic SaaS target families
- 54 public tasks
- 21 vulnerable tasks
- 33 secure controls
- 19 denial controls
- 14 authorized-allow controls

The first expansion slice adds billing entitlement coverage. The vulnerable
task checks whether a same-organization non-admin member can enable an
admin-only audit-export entitlement through the insecure route. The second
slice adds an ordered support workflow: an agent performs a legitimate status
update and then exploits a reassignment alias that fails to enforce the
admin-only boundary. Paired controls check secure agent denial, cross-org
denial, authorized admin reassignment, and status-only state preservation.

## Current Evidence

The current 54-task scripted sanity baseline passes all public tasks. It proves
that the expanded manifests, scorer, scripted oracle path, and baseline registry
agree. It does not prove model capability, leaderboard eligibility,
private-holdout performance, or v1 readiness.

The preceding 49-task public split has repeated diagnostic Kiro baselines: five
no-tools model families and one live HTTP `claude-sonnet-4.6` tool-agent family.
The tool-agent pair preserves one model-plan artifact and one tool-probe artifact
per task, correlates target-side requests for all 49 tasks in both runs, and
reports zero planner or parser failures. The 54-task expansion makes these rows
stale until rerun.

A completed boundary-reasoning calibration study audits the current public
tool-agent pair. The study finds that exploit-proven vulnerable submissions
often describe the right authorization concept in prose or alternate keys, but
do not preserve the oracle-compatible boundary vocabulary required by
`score-policy-v1`. The current zero boundary-reasoning result is therefore a
valid score-contract result, not a reason to retroactively relax scoring.

The current registry separates:

- `current_public_harness_check` for deterministic current-split sanity checks
- `current_public_stale` for formerly current rows that need rerun before live
  comparison
- `legacy_snapshot` for older historical rows
- `release_snapshots` for frozen tagged-release evidence such as v0.0

Rows marked `requires_rerun_before_current_comparison` cannot support current
54-task comparison. That marker does not imply the frozen v0.0 release snapshot
itself needs to be rerun.

## Frozen v0.0 Evidence

The frozen v0.0 public split contained 46 public tasks: 19 vulnerable tasks, 27
secure controls, 16 denial controls, and 11 authorized-allow controls. Its
public baselines include four repeated no-tools model-family rows and one
repeated live HTTP tool-agent family. These are useful diagnostics for exploit
replay, false positives, request correlation, and weak boundary reasoning, but
they are stale for current 54-task comparison.

The v0.0 report remains in
[`authzbench-saas-v0.0-technical-report.md`](authzbench-saas-v0.0-technical-report.md).
Use it when describing the tagged release snapshot. Use this v1-prep report
when describing current `main`.

## Next Work

Before a v1 release, expand task volume, implement rotating private holdouts,
complete independent external review, build hosted or fully containerized
submission infrastructure, and keep chart/table captions explicit about current
versus stale evidence. The v1/community submission governance is now defined in
`docs/v1-community-submission-governance.md`, but the hosted/containerized
runner and real external reviews are not yet complete. After any v1 task or
scoring change, rerun current public no-tools and tool-agent baselines before
making new comparisons.
