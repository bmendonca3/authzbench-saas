# Baselines

Tracked baseline files summarize reproducible runs without committing the full
`results/` directory.

## Current Baselines

- `scripted-baseline-summary.json`: deterministic harness sanity-check baseline.
- `kiro-claude-sonnet-4.6-full-summary.json`: full public split through the
  Kiro no-tools adapter.
- `kiro-qwen3-coder-next-full-summary.json`: full public split through the Kiro
  no-tools adapter.

For every model baseline, preserve:

- exact command or agent harness
- model name and version/date
- benchmark commit, tag, or release archive
- `summary.json`
- per-task scores and transcripts, or an archive path if the full result bundle
  is too large to track

The Kiro baseline adapter is a simple command wrapper around `kiro chat`. It is
useful for a first public comparison, but leaderboard-quality submissions should
also report the full agent harness, tool access, isolation settings, and result
bundle.
