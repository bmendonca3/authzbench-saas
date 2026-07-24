# Baseline Credibility

AuthZBench-SaaS should not treat every run artifact as a leaderboard result.
Baseline files need to say what they prove, what they do not prove, and whether
they are current enough for the v1.0-internal label. The registry now contains
current 63-task public-split Kiro no-tools and live HTTP tool-agent capability
rows; older 60-task, 54-task, 49-task, 46-task, and 44-task rows remain stale
or historical audit evidence. Leaderboard-candidate rows are inside the repo
evidence model, not hosted leaderboard operation, not platform acceptance, and
not third-party submissions.

## Registry

The baseline registry lives at [`../baselines/baseline-registry.json`](../baselines/baseline-registry.json).
Validate it with:

```bash
python3 scripts/validate_baseline_registry.py
```

The public validation gate also runs this registry validator.

The registry separates:

- `harness_check`: deterministic checks that prove the benchmark/scorer/targets
  are wired correctly, not model capability.
- `model_baseline`: model runs without live tool access.
- `tool_agent_baseline`: tool-using agent runs against the benchmark.

It also labels every summary as one of:

- `current_public_split`: valid for the current public task split. For model
  and tool-agent rows this can be a full current-split rerun, or an explicitly
  labeled `promoted_cohort_delta_merge` composite when a prior immutable public
  baseline is combined with fresh reruns of only the newly promoted public
  tasks. Composite rows must not be described as full reruns.
- `current_public_harness_check`: current public split, but only a deterministic
  harness sanity check.
- `current_public_stale`: previously current public-split evidence that no
  longer matches the active public task count and must be rerun before current
  comparison.
- `legacy_snapshot`: useful historical evidence that must be rerun before a
  current comparison or v1.0-internal current-split claim.

It also keeps explicit `release_snapshots`. A release snapshot names the frozen
baseline IDs and public-split counts for a tagged release such as `v0.0`, so old
46-task evidence can remain auditable after v1 task expansion without counting
as current-comparable evidence.

## v0 Baseline Bar

The baseline sub-gate currently has five repeated 63-task no-tools Kiro
model-family baselines plus one repeated 63-task live HTTP Kiro
`claude-sonnet-4.6` tool-agent family on the live public split. The frozen v0.0
46-task release snapshot remains auditable release evidence. The 60-task,
54-task, and 49-task Kiro rows are stale for current 63-task comparison, and
the old 46-task evidence remains frozen v0.0 release evidence.

The v0 baseline bar is:

- at least five real model or agent families on the current public split
- at least two runs per serious model or agent family
- at least one tool-agent baseline, not only no-tools model runs
- exact command, harness type, model label, benchmark version, commit SHA, and
  result path preserved
- current public summaries include a matching `benchmark_fingerprint` for the
  active task set, score policy, and evidence contract
- repeated runs backed by distinct `run_artifacts` files with distinct `run_id`
  values, not just a self-declared run count
- public-split and private-holdout results reported separately
- one-off or legacy snapshots excluded from local row eligibility

The validator reports `v0_baseline_ready` and `v0_release_snapshot_ready`
separately from registry consistency. That means the registry can remain
internally honest even when a future task or scoring change temporarily makes
current baseline coverage incomplete again.

The validator now enforces `benchmark_fingerprint` on current public split
evidence. The fingerprint binds the result to the public task manifests and the
current scoring/evidence contract without exposing task IDs in the fingerprint
object. Historical 44-task and legacy snapshots are allowed to remain useful
diagnostics, but they do not satisfy this current-public comparability check.

For a future current model or tool-agent row produced through an adapter,
`requires_zero_adapter_failures: true` is an opt-in promotion gate. Every primary
and repeated summary must then report one `model-output.json` artifact per task,
zero adapter failures, zero unverified model labels, and zero invalid
submissions. It must not be attached retrospectively to legacy rows whose
summaries lack compatible telemetry. This guard prevents adapter failure from
being mistaken for a valid empty secure-control submission; it does not create
fresh model evidence.

## Current Interpretation

The v0.0 scripted baseline is a 46-task deterministic harness sanity check. It
proves the scorer, task manifests, and scripted oracle path fit the frozen v0.0
public split. It is not model capability evidence and is stale for current
63-task comparison.

The current scripted baseline is a 63-task deterministic harness sanity check.
It proves the expanded v1-prep public split, scorer, and scripted oracle path
agree. It is not model capability evidence, a leaderboard-candidate row, private-holdout
evidence, or a substitute for current model or tool-agent baselines.

The stale 54-task `qwen3-coder-next` no-tools baseline has two runs on the
stale 54-task fingerprint. They pass 32 and 33 tasks, prove 0 and 3 of 21 vulnerable
replays, keep vulnerable boundary reasoning at `0.0`, and fully pass no
vulnerable task. Run 1 records two invalid submissions and seven total
task-level adapter failures plus two outer runner failures; run 2 records no
invalid submissions, twelve task-level adapter failures, and no outer runner
failure. The adapter converts an inner Kiro command or JSON-extraction failure
to a valid empty-findings fallback, so the task remains in the denominator and
can pass a secure control or fail a vulnerable task. The summaries also explain
the 60-second inner model-call timeout and 75-second outer per-task timeout.
Run 1's `0.9524` vulnerable safety rate is caused by an invalid submission from
an outer runner failure, not an unsafe action. This is stale public-split
evidence for one model family, not current 63-task evidence, private evidence,
a stable cross-model comparison, or a leaderboard-candidate row.

The stale 54-task `claude-haiku-4.5` no-tools baseline also has two runs on
the stale 54-task fingerprint. Both pass 32 tasks, prove 4 and 5 of 21 vulnerable
replays, keep boundary reasoning at `0.0`, and fully pass no vulnerable task.
They have zero adapter failures, zero outer runner failures, and zero invalid
submissions. Each reports one false finding on an authorized-allow support
reassignment control, yielding `false_positive_rate: 0.0303`,
`control_false_report_rate: 0.0303`, and `authorized_allow_pass_rate: 0.9286`.
The scorer-finding aggregates were derived exactly from retained per-task rows
because these runs immediately predate the aggregate emitter. This is stale
public evidence for a second no-tools family, not current 63-task evidence,
private evidence, a stable cross-model ranking, a leaderboard-candidate row, or v1
readiness.

The stale 54-task `claude-sonnet-4.6` no-tools baseline has two runs on the
stale 54-task fingerprint. Both pass 32 tasks and keep boundary reasoning at `0.0`,
while proving 15 and 14 of 21 vulnerable replays. They have zero adapter
failures, zero outer runner failures, and zero invalid submissions. Run 1
reports the authorized-allow admin reassignment control as vulnerable; run 2
reports the secure viewer-status denial control as vulnerable. Each has one
control false report and `false_positive_rate: 0.0303`; their authorized-allow
pass rates are `0.9286` and `1.0`. This is stale public evidence for a third
no-tools family, not current 63-task evidence, private evidence, a stable
cross-model ranking, a leaderboard-candidate row, or v1.0-internal current-split evidence.

The stale 54-task `glm-5` no-tools baseline has two runs on the stale 54-task
fingerprint. Both pass 33 tasks, keep boundary reasoning at `0.0`, fully pass
no vulnerable task, and report zero control false positives. They prove 2 and 3
of 21 vulnerable replays and have 2 and 4 scorer-counted findings. Run 1
preserves one outer runner failure on the support multistep reassignment task,
leaving submission/model-output artifacts absent and producing one invalid
submission; run 2 has complete 54-task artifacts and zero invalid submissions.
This is stale public evidence for a fourth no-tools family, not current 63-task
evidence, private evidence, a stable cross-model ranking, a leaderboard-candidate row, or
v1.0-internal current-split evidence.

The stale 54-task `claude-opus-4.6` no-tools baseline has two runs on the
stale 54-task fingerprint. Both pass 33 tasks, keep boundary reasoning at `0.0`, fully
pass no vulnerable task, and report zero control false positives. Both prove 14
of 21 vulnerable replays and have 21 scorer-counted findings. Both runs retain
complete 54-task context, submission, score, transcript, and model-output
artifacts with zero adapter, command, parser, runner, or invalid-submission
failures. This is stale public evidence for a fifth no-tools family, not
current 63-task evidence, private evidence, a stable cross-model ranking, a
leaderboard-candidate row, or v1.0-internal current-split evidence.

The stale 54-task `claude-sonnet-4.6` live HTTP Kiro tool-agent baseline has
two runs on the stale 54-task fingerprint. Both pass 33 tasks, prove 15 of 21
vulnerable replays, keep boundary reasoning at `0.0`, fully pass no vulnerable
task, and report zero secure-control false positives. Both runs write one
model-tool plan artifact and one tool-probe artifact per task, correlate
target-side requests for all 54 tasks, and report zero planner failures, zero
parser failures, zero invalid submissions, and zero fallback probes. This is
stale public live HTTP evidence for the previous 54-task split, not current
63-task evidence, private evidence, hosted-leaderboard evidence, a stable
cross-model ranking, or v1.0-internal current-split evidence.

The stale 49-task no-tools Kiro baselines have two runs each for
`claude-haiku-4.5`, `claude-sonnet-4.6`, `qwen3-coder-next`, `glm-5`, and
`claude-opus-4.6`, all using benchmark commit
`1eaac973ffe5229dad5796b9a5b144fa3af37a3a`. They remain public-split
diagnostic evidence for the preceding task fingerprint only. They are not
current 63-task, private-holdout, live HTTP tool-agent, hosted-leaderboard, or
v1 release evidence. All five families have
`boundary_reasoning_pass_rate: 0.0`.

The stale 49-task `claude-sonnet-4.6` live HTTP Kiro tool-agent baseline has
two runs using benchmark commit
`3d4293cd24305ad410ddad8cb68654bf10adc9ff`. Both runs write one
`model-tool-plan.json` and one `tool-probes.json` artifact per task, correlate
target-side requests for all 49 tasks, and report zero planner failures and zero
parser failures. Run 1 executed 124 probes and run 2 executed 126 probes; both
proved 15 of 20 vulnerable replays, produced zero secure-control false reports,
and still fully passed zero vulnerable tasks because vulnerable boundary
reasoning remained `0.0`. This evidence closed the public tool-agent evidence gate
for the preceding 49-task fingerprint only. It is stale after later task
expansions and is not current 63-task, private-holdout, hosted-leaderboard, or
v1 release evidence.

The v0.0 `qwen3-coder-next` no-tools Kiro baseline has two 46-task public runs.
It is useful historical public model evidence, but it is still not
private-holdout evidence, not a tool-agent result, not current 63-task evidence,
and not leaderboard eligible.
It also shows why repetition matters: the first run found no exploit-proven
vulnerable tasks, while the repeat found one but still had weak boundary
reasoning and one invalid submission.

The v0.0 `claude-haiku-4.5` no-tools Kiro baseline also has two 46-task public
runs. It adds a second repeated v0.0 model family, but it should not be read as
a leaderboard-candidate row or current 63-task result. Run 1 proved five vulnerable
replays but produced one secure-control false report; run 2 proved one
vulnerable replay with zero false positives. Both runs had
`boundary_reasoning_pass_rate: 0.0`, so neither fully passed a vulnerable task.
One paired run used the immediately preceding chart-only commit; no tasks, apps,
scorer, runner, or harness behavior changed between the paired SHAs.

The v0.0 `claude-sonnet-4.6` no-tools Kiro baseline has two 46-task public runs.
It adds a third repeated v0.0 no-tools model family. Run 1 proved 12 vulnerable
replays with zero control false reports; run 2 proved eight vulnerable replays
and produced one secure-control false report. Both runs had
`boundary_reasoning_pass_rate: 0.0`, so neither fully passed a vulnerable task.
They are v0.0 public-split model evidence only, not current 63-task,
private-holdout, or leaderboard-candidate rows.

The v0.0 `glm-5` no-tools Kiro baseline has two 46-task public runs. It adds a
fourth repeated v0.0 no-tools model family and satisfies the fifth repeated
v0.0 model/agent-family requirement when counted with the repeated tool-agent
family. Run 1 proved four vulnerable replays; run 2 proved one. Both runs had
zero control false reports and `boundary_reasoning_pass_rate: 0.0`, so neither
fully passed a vulnerable task. They are v0.0 public-split model evidence only,
not current 63-task, private-holdout, or leaderboard-candidate rows.

For these summaries, `boundary_reasoning_pass_rate` is evaluated over
vulnerable tasks. Controls can still have task-level boundary checks, but they
do not turn Qwen's 0.0 vulnerable-boundary rate into a broader reasoning claim.

The v0.0 `claude-sonnet-4.6` live HTTP tool-agent baseline has two 46-task
public runs. It is the repeated v0.0 tool-agent row: both runs have
target-request correlation, one `model-tool-plan.json`, and one
`tool-probes.json` for all 46 tasks. Each run passed 27 of 46 tasks, proved 14
of 19 vulnerable replays, had zero control false reports, and had no planner
failures or parse errors. Both fully passed zero vulnerable tasks because
vulnerable boundary reasoning remained `0.0`. It is still v0.0 public-split
evidence only, not a current 63-task or private-holdout leaderboard result.

The two tool-agent runs span adjacent public-doc/test/tool-agent-tooling commits
rather than identical SHAs. Their comparability rests on the matching public
task fingerprint, score policy, evidence contract, task count, agent/model
labels, and per-task artifact contract; it should not be read as exact same-SHA
variance evidence.

The older live scripted, heuristic live HTTP, no-tools Kiro model, and Kiro live
tool-agent summaries were run on previous 44-task and 46-task public splits.
They are retained as stale public snapshots because they are still useful for
methodology review, but they no longer count toward current 63-task
model-family coverage or repeated-baseline coverage.

The stale 44-task snapshots still show useful signals: zero or low false
positive rates on controls, uneven exploit-proof success, and weak boundary
reasoning for several model families. They should be read as historical
diagnostics, not current rankings.

The registry uses `requires_rerun_before_current_comparison` to mark stale rows.
That field means the row cannot support live 63-task comparison. It does not
mean the frozen v0.0 release snapshot itself needs to be rerun.

The current public scripted sanity milestone, repeated no-tools Kiro
model-family coverage, and repeated live HTTP Kiro tool-agent coverage are all
restored for the 63-task fingerprint. Public baselines must still be paired with
protected private-holdout operation before leaderboard claims.

## Reviewer validation and interpretation

Reviewers can validate the baseline registry and public validation gate with:

```bash
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_public.py --include-scripted-baseline
```

`validate_baseline_registry.py` checks registry consistency, fingerprint
binding, and release-snapshot labels. `validate_public.py` runs the full
public task suite, baseline registry, task quality gate, claim-boundary
check, and the public-view readiness fixture match.

Current scripted sanity is deterministic harness verification only. It is
not model capability evidence, not leaderboard evidence, not private-holdout
evidence, and not external validation. The current 63-task Kiro no-tools and
live HTTP tool-agent rows are public-split capability evidence only; older
60-task, 54-task, 49-task, 46-task, and 44-task rows are stale or historical
release-snapshot evidence only.
