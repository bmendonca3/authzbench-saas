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

## v0 Baseline Bar

The baseline sub-gate currently reports `v0_baseline_ready: false`. That is
intentional after the public split moved from 44 to 46 tasks for the first
project-management multi-step workflow wave. Two repeated current no-tools
model-family baselines now exist, but three more current repeated families and
a current tool-agent baseline are still required before the baseline gate is
credible enough for v0.

The v0 baseline bar is:

- at least five real model or agent families on the current public split
- at least two runs per serious model or agent family
- at least one tool-agent baseline, not only no-tools model runs
- exact command, harness type, model label, benchmark version, commit SHA, and
  result path preserved
- repeated runs backed by distinct `run_artifacts` files with distinct `run_id`
  values, not just a self-declared run count
- public-split and private-holdout results reported separately
- one-off or legacy snapshots excluded from leaderboard eligibility

The validator can pass while reporting `v0_baseline_ready: false`. That means
the registry is internally honest, not that the baseline sub-gate is complete.

## Current Interpretation

The current scripted baseline is a 46-task deterministic harness sanity check.
It proves the scorer, task manifests, and scripted oracle path still fit the
active public split. It is not model capability evidence.

The current `qwen3-coder-next` no-tools Kiro baseline has two 46-task public
runs. It is useful current public model evidence, but it is still not
private-holdout evidence, not a tool-agent result, and not leaderboard eligible.
It also shows why repetition matters: the first run found no exploit-proven
vulnerable tasks, while the repeat found one but still had weak boundary
reasoning and one invalid submission.

The current `claude-haiku-4.5` no-tools Kiro baseline also has two 46-task
public runs. It adds a second repeated current model family, but it should not
be read as a leaderboard row. Run 1 proved five vulnerable replays but produced
one secure-control false report; run 2 proved one vulnerable replay with zero
false positives. Both runs had `boundary_reasoning_pass_rate: 0.0`, so neither
fully passed a vulnerable task. One paired run used the immediately preceding
chart-only commit; no tasks, apps, scorer, runner, or harness behavior changed
between the paired SHAs.

For these summaries, `boundary_reasoning_pass_rate` is evaluated over
vulnerable tasks. Controls can still have task-level boundary checks, but they
do not turn Qwen's 0.0 vulnerable-boundary rate into a broader reasoning claim.

The older live scripted, heuristic live HTTP, no-tools Kiro model, and Kiro live
tool-agent summaries were run on the previous 44-task public split. They are
retained as stale public snapshots because they are still useful for
methodology review, but they no longer count toward current public model-family
coverage beyond the new Qwen and Haiku reruns, repeated-baseline coverage
beyond those reruns, or the current public tool-agent gate.

The stale 44-task snapshots still show useful signals: zero or low false
positive rates on controls, uneven exploit-proof success, and weak boundary
reasoning for several model families. They should be read as historical
diagnostics, not current rankings.

The next baseline milestone is to rerun three more model/agent families twice on
the 46-task split and add one live tool-agent baseline with per-task artifacts
and target-request coverage. Only after those reruns should the registry return
to `v0_baseline_ready: true`.
