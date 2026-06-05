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

The live scripted baseline is now a current 44-task harness sanity check against
the Docker targets. It is useful because it proves vulnerable proof requests can
hit the live synthetic services and correlate into target-side request logs. It
is still not leaderboard-grade live-agent evidence: the deterministic agent only
submits findings for vulnerable tasks, so secure controls are scored by replay
but are not live-exercised as agent requests.

The heuristic live HTTP prober is a stronger current harness check for live
target proof. It probes documented routes for every public task and writes a
per-task `tool-probes.json` artifact, giving full target-request correlation
across vulnerable and control tasks. Panel review classified it as deterministic
harness evidence because it uses phrase and route heuristics, so it does not
satisfy the v0 requirement for a real tool-agent baseline.

The Kiro model summaries are legacy 15-task alpha snapshots. They are useful
historical evidence, but they must be rerun on the current 44-task split and
repeated before any v0 tag or serious public leaderboard claim.

The first repeated current model family is Qwen through Kiro. The two
`qwen3-coder-next` no-tools runs are public-split baselines only: both showed
strong control restraint and zero control false-report findings. Run 2 still had
one failed denial-control score, and neither run proved vulnerable exploits.

The second repeated current model family is Sonnet through Kiro. The two
`claude-sonnet-4.6` no-tools runs are also public-split baselines only: both
passed all 26 controls and proved 14 of 18 vulnerable exploit replays, but only
3 of 18 vulnerable tasks fully passed because boundary reasoning was weak at
`0.1667`. They kept a zero false-positive rate on controls and improve
model-baseline credibility while still leaving three repeated model/agent
families, a true tool-agent baseline, and private-holdout leaderboard
submissions missing at that checkpoint.

The third repeated current model family is DeepSeek through Kiro. The two
`deepseek-3.2` no-tools runs are also public-split baselines only: both passed
26 of 44 tasks by staying quiet on controls, kept a zero false-positive rate,
and proved no vulnerable exploits. They improve baseline breadth while still
leaving two repeated model/agent families, a true tool-agent baseline, and
private-holdout leaderboard submissions missing at that checkpoint.

The fourth repeated current model family is Haiku through Kiro. The two
`claude-haiku-4.5` no-tools runs are also public-split baselines only: both
passed 26 of 44 tasks, proved 4 of 18 vulnerable replays, kept a zero
false-positive rate, and had no full vulnerable-task passes because boundary
reasoning was `0.0`. They improve baseline breadth while still leaving one
repeated model/agent family, a true tool-agent baseline, and private-holdout
leaderboard submissions missing at that checkpoint.

The fifth repeated current model family is Opus through Kiro. The two
`claude-opus-4.6` no-tools runs are also public-split baselines only: both
passed 27 of 44 tasks, proved 12 of 18 vulnerable replays, kept a zero
false-positive rate, and fully passed 1 vulnerable task because boundary
reasoning remained weak at `0.0556`. They satisfy the repeated public model
family count while still leaving a true tool-agent baseline and private-holdout
leaderboard submissions missing.
