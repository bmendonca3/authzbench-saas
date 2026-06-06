# Baselines

Tracked baseline files summarize reproducible runs without committing the full
`results/` directory.

The machine-readable registry is
[`baseline-registry.json`](baseline-registry.json). Validate it with:

```bash
python3 scripts/validate_baseline_registry.py
```

The registry is an honesty gate. It separates current public-split runs from
stale public snapshots and legacy snapshots, harness checks from model
baselines, and one-off runs from leaderboard-eligible evidence. After task or
scorer changes, it can pass consistency validation while reporting
`v0_baseline_ready: false`; that means the baseline files are well-labeled, not
that current model/tool-agent evidence is complete.

## Current And Stale Baselines

- `scripted-baseline-public-46-summary.json`: current deterministic 46-task
  harness sanity-check baseline.
- `kiro-qwen3-coder-next-current-public-46-run1-summary.json` and
  `kiro-qwen3-coder-next-current-public-46-run2-summary.json`: repeated
  current 46-task public split no-tools Qwen runs through the Kiro adapter.
  These count as one current repeated public model-family baseline, but they are
  not private-holdout, tool-agent, or leaderboard-eligible submissions.
- `kiro-claude-haiku-4.5-current-public-46-run1-summary.json` and
  `kiro-claude-haiku-4.5-current-public-46-run2-summary.json`: repeated
  current 46-task public split no-tools Haiku runs through the Kiro adapter.
  These count as one current repeated public model-family baseline, but they
  are not private-holdout, tool-agent, or leaderboard-eligible submissions.
  The paired runs span adjacent chart-only commits; task, app, scorer, runner,
  and harness behavior did not change between the paired SHAs.
- `kiro-claude-sonnet-4.6-current-public-46-run1-summary.json` and
  `kiro-claude-sonnet-4.6-current-public-46-run2-summary.json`: repeated
  current 46-task public split no-tools Sonnet runs through the Kiro adapter.
  These count as one current repeated public model-family baseline, but they
  are not private-holdout, tool-agent, or leaderboard-eligible submissions.
- `kiro-live-tool-agent-sonnet-current-public-46-summary.json` and
  `kiro-live-tool-agent-sonnet-current-public-46-run2-summary.json`: repeated
  current 46-task public split live HTTP tool-agent runs using
  `claude-sonnet-4.6` through the Kiro adapter. Both runs write one model-tool
  plan artifact and one tool-probe artifact per task, correlate target-side
  requests for all 46 tasks, and share the same public task/scoring fingerprint.
  They span adjacent public-doc/test/tool-agent-tooling commits rather than
  identical SHAs, so they remain public-split evidence only. They are not
  private-holdout or leaderboard-eligible evidence.
- `scripted-baseline-summary.json`: earlier deterministic 44-task harness
  sanity-check baseline.
- `live-scripted-baseline-summary.json`: deterministic baseline that exercises
  vulnerable proof requests against the live Docker targets before submitting.
  The stale 44-task run passes, with target-side request correlation on the 18
  vulnerable tasks. Secure controls still have no agent-side live requests in
  this harness because the deterministic agent only exercises submitted
  findings.
- `heuristic-live-http-prober-public-44-summary.json`: deterministic live HTTP
  probe harness that exercises documented routes on every public task and writes
  per-task probe artifacts. The stale run has 44/44 target-side request
  correlation and zero control false reports, but panel review classified it as
  a harness check, not the real v0 tool-agent baseline.
- `kiro-live-tool-agent-sonnet-current-public-44-summary.json`: Kiro-planned
  live HTTP tool-agent baseline using `claude-sonnet-4.6`. It writes one
  model-tool plan artifact and one tool-probe artifact per public task, executes
  100 live HTTP probes, and has 44/44 target-side request correlation. It is
  stale public-split evidence only, not current, private-holdout, or
  leaderboard-eligible evidence.
- `kiro-claude-sonnet-4.6-full-summary.json`: legacy 15-task alpha snapshot
  through the Kiro no-tools adapter.
- `kiro-qwen3-coder-next-full-summary.json`: legacy 15-task alpha snapshot
  through the Kiro no-tools adapter.
- `kiro-claude-sonnet-4.6-current-public-44-run1-summary.json` and
  `kiro-claude-sonnet-4.6-current-public-44-run2-summary.json`: repeated
  stale 44-task public split no-tools Sonnet runs through the Kiro adapter.
  They are public-split model snapshots, not current, private-holdout, or
  leaderboard-eligible submissions.
- `kiro-claude-opus-4.6-current-public-44-run1-summary.json` and
  `kiro-claude-opus-4.6-current-public-44-run2-summary.json`: repeated stale
  44-task public split no-tools Opus runs through the Kiro adapter. They are
  stale public-split model snapshots, not current, private-holdout, or
  leaderboard-eligible submissions.
- `kiro-claude-haiku-4.5-current-public-44-run1-summary.json` and
  `kiro-claude-haiku-4.5-current-public-44-run2-summary.json`: repeated
  stale 44-task public split no-tools Haiku runs through the Kiro adapter.
  They are public-split model snapshots, not current, private-holdout, or
  leaderboard-eligible submissions.
- `kiro-deepseek-3.2-current-public-44-run1-summary.json` and
  `kiro-deepseek-3.2-current-public-44-run2-summary.json`: repeated stale
  44-task public split no-tools DeepSeek runs through the Kiro adapter. They are
  stale public-split model snapshots, not current, private-holdout, or
  leaderboard-eligible submissions.
- `kiro-qwen3-coder-next-current-public-44-run1-summary.json` and
  `kiro-qwen3-coder-next-current-public-44-run2-summary.json`: repeated stale
  44-task public split no-tools Qwen runs through the Kiro adapter. They are
  stale public-split model snapshots, not current, private-holdout, or
  leaderboard-eligible submissions.

The scripted summary should match the current public split. Older Kiro and live
HTTP summaries may remain tracked as stale snapshots when the task set expands,
but they must be rerun before any tagged release or current comparison. Current
public Kiro summaries must include distinct `run_artifacts` before they count
as repeated evidence.

For every model baseline, preserve:

- exact command or agent harness
- model name and version/date
- benchmark version emitted by the runner
- benchmark commit SHA or release archive SHA
- harness type, such as `tool-agent`, `no-tools-model`, or `scripted`
- benchmark commit, tag, or release archive
- `summary.json`
- control mix fields, including denial controls and authorized-allow controls
- per-task scores and transcripts, or an archive path if the full result bundle
  is too large to track

The Kiro baseline adapter is a simple command wrapper around `kiro chat`. It is
useful for a first public comparison, but leaderboard-quality submissions should
also report the full agent harness, tool access, isolation settings, and result
bundle.

The runner supports `--benchmark-version`, `--benchmark-commit-sha`, `--agent`,
`--model`, and `--harness-type` so curated baseline summaries do not need to
invent these fields after the run.
