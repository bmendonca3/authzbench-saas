# Baselines

Tracked baseline files summarize reproducible runs without committing the full
`results/` directory.

## Current Baselines

- `scripted-baseline-summary.json`: deterministic harness sanity-check baseline.
- `live-scripted-baseline-summary.json`: deterministic baseline that exercises
  vulnerable proof requests against the live Docker targets before submitting.
- `kiro-claude-sonnet-4.6-full-summary.json`: full public split through the
  Kiro no-tools adapter.
- `kiro-qwen3-coder-next-full-summary.json`: full public split through the Kiro
  no-tools adapter.

The scripted baseline summary should match the current public split. The live
scripted and Kiro summaries may temporarily be older alpha snapshots when the
task set expands; rerun them before any tagged release.

For every model baseline, preserve:

- exact command or agent harness
- model name and version/date
- benchmark version emitted by the runner
- benchmark commit SHA or release archive SHA
- harness type, such as `tool-agent`, `no-tools-model`, or `scripted`
- benchmark commit, tag, or release archive
- `summary.json`
- per-task scores and transcripts, or an archive path if the full result bundle
  is too large to track

The Kiro baseline adapter is a simple command wrapper around `kiro chat`. It is
useful for a first public comparison, but leaderboard-quality submissions should
also report the full agent harness, tool access, isolation settings, and result
bundle.

The runner supports `--benchmark-version`, `--benchmark-commit-sha`, `--agent`,
`--model`, and `--harness-type` so curated baseline summaries do not need to
invent these fields after the run.
