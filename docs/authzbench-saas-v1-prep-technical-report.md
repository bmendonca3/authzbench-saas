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
stale for current 54-task comparison. Repeated 54-task Qwen, Claude Haiku 4.5,
and Claude Sonnet 4.6 no-tools families are now current, but they do not provide
the full model-family or tool-agent coverage required for stable comparison.

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

Two current 54-task `qwen3-coder-next` no-tools runs provide repeated diagnostic
evidence for one model family. They pass 32 and 33 tasks, span
`0.0000-0.1429` exploit-proven success, keep vulnerable boundary reasoning at
`0.0000`, and fully pass no vulnerable task. Their summaries retain seven and
twelve task-level adapter failures, including inner Kiro command failures and
outputs without a usable submission object. Those failures become valid
empty-findings fallbacks that remain in the scored denominator; the first run
also has two outer runner failures that become invalid submissions. The pair is
public-split evidence only and does not close the remaining no-tools or live
HTTP tool-agent rerun gates.

Two current 54-task `claude-haiku-4.5` no-tools runs provide a second repeated
model family. Both pass 32 tasks, prove 4 and 5 of 21 vulnerable replays, keep
boundary reasoning at `0.0000`, and fully pass no vulnerable task. Both have
zero adapter failures, zero outer runner failures, and zero invalid
submissions. Each reports one false finding on the authorized-allow support
reassignment control, producing `false_positive_rate: 0.0303`,
`control_false_report_rate: 0.0303`, and `authorized_allow_pass_rate: 0.9286`.
This pair improves current evidence breadth but remains public-split diagnostic
evidence, not a stable ranking.

Two current 54-task `claude-sonnet-4.6` no-tools runs provide a third repeated
model family. Both pass 32 tasks, prove 15 and 14 of 21 vulnerable replays,
keep boundary reasoning at `0.0000`, and fully pass no vulnerable task. Both
have zero adapter failures, zero outer runner failures, and zero invalid
submissions. Run 1 reports the authorized-allow admin reassignment control as
vulnerable; run 2 reports the secure viewer-status denial control as
vulnerable. Each has `false_positive_rate: 0.0303` and
`control_false_report_rate: 0.0303`, while their authorized-allow pass rates
are `0.9286` and `1.0`. This is stronger public exploit-replay evidence, not a
stable ranking.

The preceding 49-task public split has repeated diagnostic Kiro baselines: five
no-tools model families and one live HTTP `claude-sonnet-4.6` tool-agent family.
The tool-agent pair preserves one model-plan artifact and one tool-probe artifact
per task, correlates target-side requests for all 49 tasks in both runs, and
reports zero planner or parser failures. The 54-task expansion makes these rows
stale; only the Qwen, Claude Haiku 4.5, and Claude Sonnet 4.6 no-tools families
have been rerun so far.

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

Before a v1 release, complete the remaining 54-task no-tools and live HTTP
tool-agent reruns, expand task volume, implement rotating private holdouts,
complete independent external review, build hosted or fully containerized
submission infrastructure, and keep chart/table captions explicit about current
versus stale evidence. The v1/community submission governance is now defined in
`docs/v1-community-submission-governance.md`, but the hosted/containerized
runner and real external reviews are not yet complete. After any v1 task or
scoring change, rerun current public no-tools and tool-agent baselines before
making new comparisons.
