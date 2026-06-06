# Repeated Tool-Agent Baseline Panel Summary

Date: 2026-06-06

Scope: second current public 46-task live HTTP tool-agent run, baseline registry
updates, chart data, and public claim wording.

## Counted Reviewers

- Gemini 3.5 Flash (High), verified by Antigravity CLI log
- Gemini 3.1 Pro (High), verified by Antigravity CLI log
- Kiro CLI `claude-opus-4.8`, verified by live model catalog and Kiro output
- Parent ChatGPT reviewer

Claude Sonnet 4.6 and Claude Opus 4.6 Antigravity labels were verified by logs
but did not return substantive review text for this checkpoint, so they are not
counted as substantive reviewers.

Raw prompts and logs are kept under ignored `docs/reviews/panel-logs/` and are
not part of the public release artifact.

## Consensus

Reviewers agreed that the second current public tool-agent run improves
credibility because it is real repeated public-split evidence, not an inflated
run count:

- both runs have distinct `run_id` values
- both runs have the same 46-task benchmark fingerprint
- both runs have 46/46 model-plan artifacts
- both runs have 46/46 tool-probe artifacts
- both runs have 46/46 target-request correlation
- both runs pass 27 of 46 tasks, prove 14 of 19 vulnerable replays, produce zero
  secure-control false reports, and keep vulnerable boundary reasoning at `0.0`

The panel also agreed that the public claim boundary remains intact:
`v0_baseline_ready` is still `false`, the runs are not private-holdout evidence,
and the docs do not claim hosted leaderboard readiness.

## Accepted Findings

1. `docs/launch-report.md` had one paragraph where stale 44-task Sonnet
   no-tools runs could be confused with the current Sonnet tool-agent runs.

Disposition: accepted. The paragraph now explicitly says "stale 44-task Opus
no-tools" and "stale 44-task Sonnet no-tools" before discussing those rows.

2. The repeated tool-agent outcome is deterministic in the headline metrics.

Disposition: accepted as a claim boundary. The repeat supports reproducibility
on the current public split, not variance robustness under randomized prompts or
private holdouts.

3. Uniform `0.0` vulnerable boundary reasoning should remain visible.

Disposition: accepted. Public docs keep the `0.0` boundary-reasoning result and
state that the tool-agent fully passes zero vulnerable tasks despite proving
14/19 vulnerable replays.

## Claim Boundary

This checkpoint supports this claim:

`AuthZBench-SaaS now has a repeated current public live HTTP tool-agent baseline
with per-task planning artifacts, probe artifacts, and full target-request
correlation.`

It does not support:

- v0 or v1 readiness
- hosted leaderboard readiness
- private-holdout tool-agent performance
- variance robustness
- strong authorization-boundary reasoning by the current tool-agent

## Verification

Required verification for this checkpoint:

- `python3 scripts/validate_baseline_registry.py`
- `python3 scripts/validate_v0_release.py --allow-incomplete`
- `python3 scripts/generate_benchmark_charts.py`
- `python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'`
- full public validation
- privacy check proving raw panel logs, private holdouts, results, and captures
  are untracked
- remote CI after commit
