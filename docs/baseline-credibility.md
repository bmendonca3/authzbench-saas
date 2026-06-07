# Baseline Credibility

AuthZBench-SaaS should not treat every run artifact as a leaderboard result.
Baseline files need to say what they prove, what they do not prove, and whether
they are current enough to support a release claim.

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

- `current_public_split`: run on the current public task split.
- `current_public_harness_check`: current public split, but only a deterministic
  harness sanity check.
- `current_public_stale`: previously current public-split evidence that no
  longer matches the active public task count and must be rerun before v0.
- `legacy_snapshot`: useful historical evidence that must be rerun before a
  release tag.

It also keeps explicit `release_snapshots`. A release snapshot names the frozen
baseline IDs and public-split counts for a tagged release such as `v0.0`, so old
46-task evidence can remain auditable after v1 task expansion without counting
as current-comparable evidence.

## v0 Baseline Bar

The baseline sub-gate currently reports `v0_baseline_ready: false` for the live
49-task public split and `v0_release_snapshot_ready: true` for the frozen v0.0
46-task release snapshot. The old 46-task evidence includes five repeated
model/agent families: four no-tools model-family baselines and one live HTTP
tool-agent family.

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
- one-off or legacy snapshots excluded from leaderboard eligibility

The validator reports `v0_baseline_ready` and `v0_release_snapshot_ready`
separately from registry consistency. That means the registry can remain
internally honest even when a future task or scoring change temporarily makes
current baseline coverage incomplete again.

The validator now enforces `benchmark_fingerprint` on current public split
evidence. The fingerprint binds the result to the public task manifests and the
current scoring/evidence contract without exposing task IDs in the fingerprint
object. Historical 44-task and legacy snapshots are allowed to remain useful
diagnostics, but they do not satisfy this current-public comparability check.

## Current Interpretation

The v0.0 scripted baseline is a 46-task deterministic harness sanity check. It
proves the scorer, task manifests, and scripted oracle path fit the frozen v0.0
public split. It is not model capability evidence and is stale for current
49-task comparison.

The v0.0 `qwen3-coder-next` no-tools Kiro baseline has two 46-task public runs.
It is useful historical public model evidence, but it is still not
private-holdout evidence, not a tool-agent result, not current 49-task evidence,
and not leaderboard eligible.
It also shows why repetition matters: the first run found no exploit-proven
vulnerable tasks, while the repeat found one but still had weak boundary
reasoning and one invalid submission.

The v0.0 `claude-haiku-4.5` no-tools Kiro baseline also has two 46-task public
runs. It adds a second repeated v0.0 model family, but it should not be read as
a leaderboard row or current 49-task result. Run 1 proved five vulnerable
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
They are v0.0 public-split model evidence only, not current 49-task,
private-holdout, or leaderboard rows.

The v0.0 `glm-5` no-tools Kiro baseline has two 46-task public runs. It adds a
fourth repeated v0.0 no-tools model family and satisfies the fifth repeated
v0.0 model/agent-family requirement when counted with the repeated tool-agent
family. Run 1 proved four vulnerable replays; run 2 proved one. Both runs had
zero control false reports and `boundary_reasoning_pass_rate: 0.0`, so neither
fully passed a vulnerable task. They are v0.0 public-split model evidence only,
not current 49-task, private-holdout, or leaderboard rows.

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
evidence only, not a current 49-task or private-holdout leaderboard result.

The two tool-agent runs span adjacent public-doc/test/tool-agent-tooling commits
rather than identical SHAs. Their comparability rests on the matching public
task fingerprint, score policy, evidence contract, task count, agent/model
labels, and per-task artifact contract; it should not be read as exact same-SHA
variance evidence.

The older live scripted, heuristic live HTTP, no-tools Kiro model, and Kiro live
tool-agent summaries were run on previous 44-task and 46-task public splits.
They are retained as stale public snapshots because they are still useful for
methodology review, but they no longer count toward current 49-task
model-family coverage or repeated-baseline coverage.

The stale 44-task snapshots still show useful signals: zero or low false
positive rates on controls, uneven exploit-proof success, and weak boundary
reasoning for several model families. They should be read as historical
diagnostics, not current rankings.

The next baseline milestone is not another count-filling rerun. It is to keep
the frozen v0.0 release snapshot separate from future current-public evidence,
then rerun the scripted, no-tools, and tool-agent baselines after any v1 task or
scoring change before making new comparisons.
