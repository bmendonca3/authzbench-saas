# Current 54-Task Haiku Evidence Review Summary

Status: promotion review complete. This is internal review evidence, not one of
the three required external v1 review lanes.

## Scope

The review covers:

- both current 54-task `claude-haiku-4.5` no-tools summaries;
- raw-to-promoted metric and artifact-count fidelity;
- active fingerprint and run-provenance consistency;
- baseline registry and current/stale semantics;
- scorer-derived versus adapter-reported finding totals;
- numerical claims in variance, credibility, status, launch, report, paper,
  evidence/claims, benchmark-card, and goal documents;
- current public, stale public, private, leaderboard, and v1 claim boundaries.

## Raw Evidence

- Run `20260607T185502191241Z-ac053a0a`: 54 tasks, 32 passed,
  `mean_score: 0.6815`, 4/21 exploit-proven vulnerable tasks,
  `boundary_reasoning_pass_rate: 0.0`, zero vulnerable full passes,
  `false_positive_rate: 0.0303`, `authorized_allow_pass_rate: 0.9286`, zero
  invalid submissions, and 11 scorer-counted findings.
- Run `20260607T190024255303Z-8f2cac6a`: 54 tasks, 32 passed,
  `mean_score: 0.6954`, 5/21 exploit-proven vulnerable tasks,
  `boundary_reasoning_pass_rate: 0.0`, zero vulnerable full passes,
  `false_positive_rate: 0.0303`, `authorized_allow_pass_rate: 0.9286`, zero
  invalid submissions, and 12 scorer-counted findings.
- Each raw bundle contains 54 task directories and 54 each of `score.json`,
  `submission.json`, `model-output.json`, and `agent.json`.
- Both runs have zero nonzero agent return codes, zero model-output failures,
  and the same current 54-task fingerprint.

## Interpretation

Both runs report one false finding on
`sup_admin_reassignment_control`, an authorized-allow secure control. The
backend control replay passes, so this is an agent false report rather than
target corruption. Both runs are public-split diagnostics only.

The base summaries completed immediately before the runner began emitting
`scored_submission_finding_total`. Promotion adds 11 and 12 as exact sums of
the retained per-task `submission_finding_count` values and labels that
derivation explicitly. No other run metric is reconstructed.

## Independent Audit

- A broad Kiro Claude Opus 4.8 audit independently confirmed raw-to-promoted
  finding totals and chart aggregation, then identified an ambiguous
  `vulnerable_safety_pass_rate` attribution in the variance analysis. The prose
  now explicitly identifies that value as Qwen run 1. The audit later stalled
  without a final verdict and is excluded from completion evidence.
- A narrower replacement Kiro Claude Opus 4.6 audit reread the corrected raw
  summaries, promoted summaries, registry, chart data, tests, goal, review
  records, report, status, launch report, and paper. It returned
  `VERDICT: CLEAN` after reconciling the 11/12 finding totals, zero-failure
  diagnostics, repeated authorized-allow false report, 54-task fingerprint,
  registry counts, chart means, goal status, and public-only claim boundaries.
- Exact logs are retained locally at
  `/tmp/authzbench-kiro-opus-haiku-54-promotion-audit.txt` and
  `/tmp/authzbench-kiro-opus-haiku-54-replacement-audit.txt`. They are review
  inputs, not tracked benchmark evidence.

## Local Verification

- `python3 -m unittest discover -s tests`: 193 tests passed.
- `python3 scripts/validate_public.py --include-scripted-baseline`: passed,
  including the 54-task deterministic baseline and generated-artifact checks.
- `python3 scripts/validate_v0_release.py`: all eight frozen-v0 gates passed.
- Baseline-registry and leaderboard-submission validation passed; the current
  public view correctly remains red at two of five repeated model families and
  no current tool-agent family.
- Both raw bundles contain 54 task directories and 54 each of `score.json`,
  `submission.json`, `model-output.json`, and `agent.json`.
- Across all 108 `model-output.json` files, return codes are zero, `parse_error`
  is absent, and stdout is nonempty.
- Repeated chart generation produced byte-identical files.
- Repeated paper-table generation produced byte-identical files.
- The IEEE paper compiled successfully. No unresolved citation, reference,
  overfull-box, fatal, or LaTeX error was present; the existing font and
  underfull-box warnings remain nonblocking.
- `git diff --check` passed and the tracked private/raw-path scan was empty.

## Remote Verification

Promotion commit `a1b8b000d1b4789d03f780c969224e69f08f7b2f` and
paper-preflight commit `9cd06e2b017a3071ccb398026654c78e949fbe3f` are
authored as `bmendonca3` and pushed to `main` and `v1-task-expansion`.
Exact-head GitHub Actions run `27102791303` passed on the preflight commit.
