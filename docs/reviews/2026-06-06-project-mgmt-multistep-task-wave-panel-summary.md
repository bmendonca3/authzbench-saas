# Project Management Multi-Step Task Wave Panel Summary

Date: 2026-06-06

Scope: first public task wave that uses `evidence_requirements`, the matching
project-management control task, the 46-task scripted summary, stale 44-task
baseline handling, chart updates, and related docs/tests.

## Counted Reviewers

- Gemini 3.1 Pro (High), verified by Antigravity CLI log
- Gemini 3.5 Flash (High), verified by Antigravity CLI log
- Kiro CLI `claude-opus-4.8`, verified against the live Kiro model catalog
- ChatGPT reviewer, read-only staged-diff review

Claude Sonnet 4.6 and Claude Opus 4.6 Antigravity labels propagated, but they
returned no substantive review output, so they were not counted.

Raw prompts and logs are kept under ignored `docs/reviews/panel-logs/` and are
not part of the public release artifact.

## Consensus

Reviewers agreed that this checkpoint improves workflow realism and benchmark
credibility without making a v0, leaderboard-ready, or current model-comparison
claim.

The new vulnerable task requires a same-tenant Beta status update followed by a
cross-tenant Alpha alias read. The scorer now has an actual public manifest that
uses the multi-step evidence contract, and the matching control keeps normal
same-tenant owner updates from being treated as vulnerabilities.

Reviewers also agreed on the boundary: this is workflow evidence sequencing, not
a causal stateful exploit chain. The setup step is authorized workflow context;
the alias read remains the vulnerable authorization failure.

The public split has changed from 44 to 46 tasks. Reviewers agreed that the old
44-task model and tool-agent baselines must be treated as stale comparison
artifacts until rerun on the 46-task split.

## Accepted Findings

1. The first project-management multi-step wave improves scorer-enforced
   workflow evidence, but the target app remains intentionally simple and does
   not yet model deeper backend state dependencies between the setup write and
   the final alias read.

Disposition: accepted as a boundary. This wave is a public proof of the
multi-step evidence contract, not the final v1 workflow-realism bar.

2. The docs initially listed the strict release validator as a successful local
   check even though strict v0 readiness is expected to fail after stale baseline
   invalidation.

Disposition: accepted and fixed. `docs/status.md` now lists
`validate_v0_release.py --allow-incomplete` as the successful public-scaffold
check and separately states that strict `validate_v0_release.py` is expected to
report `v0_ready: false` until the 46-task model/tool-agent baselines are rerun.

3. Partial multi-step evidence needed direct verification against the actual new
   manifest.

Disposition: accepted and hardened. The harness tests now exercise the new
`pm_multistep_beta_update_then_alpha_alias_read` manifest directly for full
credit, missing-step failure, and duplicate-final-step failure.

4. Stale model/tool-agent chart rows could still look current if readers skimmed
   only the metric bars.

Disposition: accepted and fixed. Stale baseline rows now render in muted gray,
and the chart text still marks them as rerun-required.

## Claim Boundary

This checkpoint supports the public claim:

`alpha/pre-v0 public benchmark scaffold with first multi-step workflow evidence
task wave and stale-baseline invalidation.`

It does not support these claims yet:

- v0 release
- leaderboard-ready benchmark
- current 46-task model leaderboard
- current public tool-agent baseline
- private-holdout model ranking

## Verification

Required verification for this checkpoint:

- actual-manifest multi-step scorer tests
- full unit suite
- public manifest validation
- scripted 46-task public baseline
- baseline registry validation showing `v0_baseline_ready: false`
- public validation with scripted baseline
- v0 release validation with `--allow-incomplete`
- privacy check proving raw panel logs, private holdouts, results, and captures
  are untracked
- remote CI after commit
