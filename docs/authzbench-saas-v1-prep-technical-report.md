# AuthZBench-SaaS v1-Prep Technical Report Draft

Status: current-main v1-prep draft. This document describes the active
post-v0 development state while preserving the frozen v0.0 claim boundary.

## Claim Boundary

AuthZBench-SaaS v0.0 is the released historical artifact. Current `main` is now
post-v0 active development. It contains two v1 task-expansion slices and a
60-task public split, but it is not a v1 release, a hosted leaderboard, or a
community-scale benchmark.

The frozen v0.0 evidence remains auditable at the 46-task release boundary. The
46-task release baselines, 49-task v1-prep model/tool-agent baselines, and
54-task v1-prep model/tool-agent baselines are stale for current 63-task
comparison. Repeated 54-task Qwen, Claude Haiku 4.5, Claude Sonnet 4.6, GLM-5,
and Claude Opus 4.6 no-tools families plus the repeated 54-task Claude Sonnet
4.6 live HTTP tool-agent family remain public-split diagnostic evidence only;
they do not provide current 63-task comparison, private-holdout,
hosted-leaderboard, or v1 release evidence.

## Current Public Split

The current v1-prep public split contains:

- 6 synthetic SaaS target families
- 63 public tasks
- 27 vulnerable tasks
- 36 secure controls
- 21 denial controls
- 15 authorized-allow controls

The first expansion slice adds billing entitlement coverage. The vulnerable
task checks whether a same-organization non-admin member can enable an
admin-only audit-export entitlement through the insecure route. The second
slice adds an ordered support workflow: an agent performs a legitimate status
update and then exploits a reassignment alias that fails to enforce the
admin-only boundary. Paired controls check secure agent denial, cross-org
denial, authorized admin reassignment, and status-only state preservation.

## Current Evidence

The current 63-task scripted sanity baseline passes all public tasks. It proves
that the expanded manifests, scorer, scripted oracle path, and baseline registry
agree. It does not prove model capability, leaderboard eligibility,
private-holdout performance, or v1 readiness.

Two stale 54-task `qwen3-coder-next` no-tools runs provide repeated diagnostic
evidence for one model family. They pass 32 and 33 tasks, span
`0.0000-0.1429` exploit-proven success, keep vulnerable boundary reasoning at
`0.0000`, and fully pass no vulnerable task. Their summaries retain seven and
twelve task-level adapter failures, including inner Kiro command failures and
outputs without a usable submission object. Those failures become valid
empty-findings fallbacks that remain in the scored denominator; the first run
also has two outer runner failures that become invalid submissions. The pair is
public-split evidence only.

Two stale 54-task `claude-haiku-4.5` no-tools runs provide a second repeated
model family. Both pass 32 tasks, prove 4 and 5 of 21 vulnerable replays, keep
boundary reasoning at `0.0000`, and fully pass no vulnerable task. Both have
zero adapter failures, zero outer runner failures, and zero invalid
submissions. Each reports one false finding on the authorized-allow support
reassignment control, producing `false_positive_rate: 0.0303`,
`control_false_report_rate: 0.0303`, and `authorized_allow_pass_rate: 0.9286`.
This pair remains stale diagnostic evidence but remains public-split diagnostic
evidence, not a stable ranking.

Two stale 54-task `claude-sonnet-4.6` no-tools runs provide a third repeated
model family. Both pass 32 tasks, prove 15 and 14 of 21 vulnerable replays,
keep boundary reasoning at `0.0000`, and fully pass no vulnerable task. Both
have zero adapter failures, zero outer runner failures, and zero invalid
submissions. Run 1 reports the authorized-allow admin reassignment control as
vulnerable; run 2 reports the secure viewer-status denial control as
vulnerable. Each has `false_positive_rate: 0.0303` and
`control_false_report_rate: 0.0303`, while their authorized-allow pass rates
are `0.9286` and `1.0`. This is stronger public exploit-replay evidence, not a
stable ranking.

Two stale 54-task `glm-5` no-tools runs provide a fourth repeated model
family. Both pass 33 tasks, prove 2 and 3 of 21 vulnerable replays, keep
boundary reasoning at `0.0000`, fully pass no vulnerable task, and report zero
control false positives. Run 1 preserves one outer runner failure on the
support multistep reassignment task with missing submission/model-output
diagnostics; run 2 has complete 54-task artifacts and zero invalid submissions.
This remains stale no-tools diagnostic evidence, but remains public-split diagnostic
evidence rather than a stable ranking.

Two stale 54-task `claude-opus-4.6` no-tools runs provide a fifth repeated
model family. Both pass 33 tasks, prove 14 of 21 vulnerable replays, keep
boundary reasoning at `0.0000`, fully pass no vulnerable task, and report zero
control false positives. Both retain complete 54-task artifacts with zero
adapter, command, parser, runner, or invalid-submission failures. This closes
the previous 54-task no-tools rerun gate while remaining public-split diagnostic
evidence rather than private-holdout, leaderboard, or v1-release evidence.

Two stale 54-task `claude-sonnet-4.6` live HTTP tool-agent runs provide
repeated diagnostic evidence for the previous 54-task live-target harness. Both pass 33
tasks, prove 15 of 21 vulnerable replays, keep boundary reasoning at `0.0000`,
fully pass no vulnerable task, and report zero secure-control false positives.
Both runs retain 54 model-tool plan artifacts, 54 tool-probe artifacts, 54/54
target-request correlation, zero planner failures, zero planner parse errors,
zero invalid submissions, and zero fallback probes. This closes the previous
54-task live HTTP rerun gate while remaining stale public-split diagnostic
evidence rather than current 63-task, private-holdout, hosted-leaderboard, or
v1-release evidence.

The preceding 49-task public split has repeated diagnostic Kiro baselines: five
no-tools model families and one live HTTP `claude-sonnet-4.6` tool-agent family.
The tool-agent pair preserves one model-plan artifact and one tool-probe artifact
per task, correlates target-side requests for all 49 tasks in both runs, and
reports zero planner or parser failures. The 54-task expansion makes these rows
stale; Qwen, Claude Haiku 4.5, Claude Sonnet 4.6, GLM-5, Claude Opus 4.6
no-tools families, and the live HTTP tool-agent family were rerun on the now
stale 54-task fingerprint.

A completed boundary-reasoning calibration study audits the historical 49-task
public tool-agent pair. The study finds that exploit-proven vulnerable
submissions often describe the right authorization concept in prose or alternate
keys, but do not preserve the oracle-compatible boundary vocabulary required by
`score-policy-v1`. The stale 54-task tool-agent pair repeats the same
high-exploit-proof, zero-boundary-credit pattern, but the calibration study
itself remains scoped to the 49-task checkpoint. The zero boundary-reasoning
result is therefore a valid score-contract result, not a reason to
retroactively relax scoring.

The current registry separates:

- `current_public_harness_check` for deterministic current-split sanity checks
- `current_public_stale` for formerly current rows that need rerun before live
  comparison
- `legacy_snapshot` for older historical rows
- `release_snapshots` for frozen tagged-release evidence such as v0.0

Rows marked `requires_rerun_before_current_comparison` cannot support current
63-task comparison. That marker does not imply the frozen v0.0 release snapshot
itself needs to be rerun.

## Frozen v0.0 Evidence

The frozen v0.0 public split contained 46 public tasks: 19 vulnerable tasks, 27
secure controls, 16 denial controls, and 11 authorized-allow controls. Its
public baselines include four repeated no-tools model-family rows and one
repeated live HTTP tool-agent family. These are useful diagnostics for exploit
replay, false positives, request correlation, and weak boundary reasoning, but
they are stale for current 63-task comparison.

The v0.0 report remains in
[`authzbench-saas-v0.0-technical-report.md`](authzbench-saas-v0.0-technical-report.md).
Use it when describing the tagged release snapshot. Use this v1-prep report
when describing current `main`.

## Next Work

Before a v1 release, expand task volume, implement rotating private holdouts,
complete independent external review, build hosted or fully containerized
submission infrastructure, collect repeated private no-tools and tool-agent
evidence, and keep chart/table captions explicit about current versus stale
evidence. The v1/community submission governance is now defined in
`docs/v1-community-submission-governance.md`, but the hosted/containerized
runner and real external reviews are not yet complete. After any v1 task or
scoring change, rerun current public no-tools and tool-agent baselines before
making new comparisons.
