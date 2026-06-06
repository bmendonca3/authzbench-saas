# GLM Current Public 46 Panel Summary

Date: 2026-06-06

Scope: two current-public 46-task no-tools Kiro `glm-5` baseline summaries,
baseline registry update, generated chart data, roadmap maturity framing, and
public claim wording.

## Counted Reviewers

- Kiro CLI `qwen3-coder-next`, read-only file review
- Parent reviewer synthesis with local validator evidence

Raw command output is not committed. The public summary records only the
disposition and evidence needed to audit the checkpoint.

## Consensus

The GLM repeat supports the Level 1/v0 baseline-credibility sub-gate because:

- both GLM summaries contain 46 public tasks
- both runs use model `glm-5`, agent `kiro_baseline_agent`, and harness
  `no-tools-model`
- both runs use the same benchmark commit SHA, score policy, evidence contract,
  task count, and public task fingerprint
- the registry lists two distinct run artifacts with distinct run IDs
- `python3 scripts/validate_baseline_registry.py` reports five current repeated
  model/agent families and `v0_baseline_ready: true`

## Claim Boundary

Supported claim:

`AuthZBench-SaaS now has five repeated current public model/agent-family
baselines on the 46-task split, including four no-tools model families and one
live HTTP tool-agent family.`

Unsupported claims:

- hosted leaderboard readiness
- v1-scale community benchmark status
- private-holdout model ranking performance
- research-artifact status with independent external validation
- fully solved vulnerable workflows; GLM vulnerable full-pass count remains `0`

## Required Parent Verification

- `python3 scripts/validate_baseline_registry.py`
- `python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'`
- `python3 scripts/validate_v0_release.py --allow-incomplete`
- regenerated chart assets from `python3 scripts/generate_benchmark_charts.py`
- privacy check proving raw results, private holdouts, captures, and panel logs
  are untracked
- remote CI after commit
