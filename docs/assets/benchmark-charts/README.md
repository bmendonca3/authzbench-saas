# Benchmark Charts

Generated public-safe charts for AuthZBench-SaaS.

Regenerate with:

```bash
python3 scripts/generate_benchmark_charts.py
```

These charts summarize tracked public-split baselines and redacted
private-evidence summaries. Stale public baselines need rerun before
current comparison, and these charts are not hosted leaderboard rankings.

Included charts:

- `current-public-baselines.svg`: compact multi-metric overview
- `model-pass-rate.svg`: model pass rate
- `exploit-proven-success.svg`: vulnerable-task exploit proof
- `false-positive-rate.svg`: secure-control false-positive rate
- `boundary-reasoning.svg`: authorization-boundary reasoning
- `boundary-field-coverage.svg`: diagnostic policy-v2 boundary-field coverage
- `invalid-submission-rate.svg`: malformed and fail-closed execution output rate
- `task-mix.svg`: public and redacted private task mix
- `evidence-readiness.svg`: current evidence gaps
