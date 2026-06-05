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
- `legacy_snapshot`: useful historical evidence that must be rerun before a
  release tag.

## v0 Baseline Bar

The registry is intentionally not v0-ready yet. The v0 baseline bar is:

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
the registry is honest and internally consistent, not that v0 baseline evidence
is complete.

## Current Interpretation

The current scripted baseline is a harness sanity check on the 44-task public
split. It is valuable because it proves the scorer and task manifests are still
coherent.

The live scripted baseline and Kiro model summaries are legacy 15-task alpha
snapshots. They are useful historical evidence, but they must be rerun on the
current 44-task split and repeated before any v0 tag or serious public
leaderboard claim.
