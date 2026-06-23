# Benchmark Chart Assets Panel Summary

Date: 2026-06-06

Scope: generated public-safe benchmark charts under
`docs/assets/benchmark-charts/`, the chart generator, and README/docs references.

## Counted Reviewers

- Gemini 3.5 Flash (High), verified by the panel runner CLI log
- Gemini 3.1 Pro (High), verified by the panel runner CLI log
- read-only reviewer

Claude panel runner labels were verified by logs but did not return substantive
review text for this checkpoint. Kiro was intentionally skipped because the
previous narrow checkpoint had a Kiro timeout.

Raw prompts and logs are kept under ignored `docs/reviews/panel-logs/` and are
not part of the public release artifact.

## Consensus

Reviewers agreed the charts improve readability and transparency without turning
public-split baselines into private leaderboard rankings. The assets use tracked
public-safe JSON only:

- baseline registry and baseline summary JSON
- redacted protected-private summary JSON
- no private task bodies, seeds, routes, oracle bodies, raw logs, or local
  result bundles

## Accepted Findings

1. Private-holdout task mix was taken from the first redacted private summary.

Disposition: accepted and hardened. The generator now validates that redacted
private summaries are public-safe and have a consistent task mix before drawing
the private-holdout chart.

2. False-positive rate is a lower-is-better metric.

Disposition: accepted. The baseline chart now labels false-positive rate as
lower-is-better.

3. Generated charts could drift from source JSON.

Disposition: accepted. Public validation now regenerates benchmark charts and
fails if tracked chart assets differ from the generated output.

4. Baseline registry tests and status docs were stale after the new current
46-task tool-agent row.

Disposition: accepted. The registry test expectations and public docs were
updated to show the current tool-agent baseline while preserving
`v0_baseline_ready: false`.

## Claim Boundary

These charts are evidence-readability assets. They are not:

- hosted leaderboard rankings
- v1 external validation
- proof that public-split scores equal private-holdout performance

## Verification

Required verification for this checkpoint:

- `python3 scripts/generate_benchmark_charts.py`
- JSON validation for `docs/assets/benchmark-charts/chart-data.json`
- SVG structural checks
- markdown local-link checks
- full public validation
- strict v0 release gate
- privacy check proving raw panel logs, private holdouts, results, and captures
  are untracked
- remote CI after commit
