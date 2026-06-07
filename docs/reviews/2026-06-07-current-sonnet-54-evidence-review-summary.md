# Current 54-Task Sonnet Evidence Review Summary

Status: promotion gate complete. This is internal review evidence, not one of
the three required external v1 review lanes.

## Scope

The review covers both current 54-task `claude-sonnet-4.6` no-tools summaries,
raw-to-promoted fidelity, fingerprint and run provenance, adapter diagnostics,
control false reports, registry counts, charts, tests, prose, and claim
boundaries.

## Raw Evidence

- Run `20260607T194520410841Z-23511868`: 54 tasks, 32 passed,
  `mean_score: 0.8343`, 15/21 exploit-proven vulnerable tasks, zero boundary
  reasoning, zero vulnerable full passes, `false_positive_rate: 0.0303`,
  `authorized_allow_pass_rate: 0.9286`, zero invalid submissions, and 22
  scorer-counted findings.
- Run `20260607T195114220157Z-ad7ce734`: 54 tasks, 32 passed,
  `mean_score: 0.8204`, 14/21 exploit-proven vulnerable tasks, zero boundary
  reasoning, zero vulnerable full passes, `false_positive_rate: 0.0303`,
  `authorized_allow_pass_rate: 1.0`, zero invalid submissions, and 21
  scorer-counted findings.
- Each raw bundle contains 54 task directories and 54 each of `score.json`,
  `submission.json`, `model-output.json`, and `agent.json`.
- Across all 108 model outputs, return codes are zero, `parse_error` is absent,
  and stdout is nonempty.

## Interpretation

Run 1 falsely reports `sup_admin_reassignment_control`, an authorized-allow
control. Run 2 falsely reports `sup_secure_viewer_status_control`, a denial
control. Both backend control replays pass, so these are agent false reports,
not target corruption. The promoted summaries retain runner-emitted finding
totals and add only public-safe artifact-review diagnostics.

## Independent Audit

- Kiro Claude Opus 4.8 independently reconciled raw and promoted summaries,
  task-bundle completeness, fingerprint provenance, denominator math, finding
  totals, zero-failure diagnostics, registry implications, and chart means. It
  returned `VERDICT: CLEAN`.
- Kiro Claude Opus 4.6 independently audited the tests, documentation, paper,
  readiness fixture, historical/current labels, and claim boundaries. It
  returned `VERDICT: CLEAN` and noted one low-severity regression-test gap:
  the test named both false-report tasks but did not explicitly assert their
  different control types or per-run authorized-allow pass rates. The test now
  asserts both distinctions.
- Parent verification independently stripped the declared promotion-only keys
  from each promoted summary and obtained an exact JSON match to its raw
  runner summary. Parent inspection also confirmed 54 complete task bundles per
  run, zero nonzero model exits, zero parse errors, and nonempty stdout across
  all 108 model outputs.
- The post-fix Kiro Claude Opus 4.6 audit verified the strengthened regression
  assertions and returned `VERDICT: CLEAN`.

## Local Verification

- `python3 -m unittest discover -s tests`: 194 tests passed.
- `python3 scripts/validate_public.py --include-scripted-baseline`: passed,
  including the 54/54 deterministic scripted run.
- Strict v0 release, baseline-registry, and leaderboard-submission validation
  passed.
- Chart and paper-table generators were stable across repeated SHA-256
  snapshots.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` produced the
  IEEE paper PDF. Reported warnings were underfull boxes and the existing
  bibliography rerun warning; no undefined citation, undefined reference, or
  fatal error was present.
- `git diff --check` passed and the tracked private/raw-path scan was empty.
- Local container smoke was not rerun because the Docker Desktop socket was
  unavailable. Exact-head GitHub Actions run `27103482713` passed public
  validation on preflight commit
  `c3c3d702d1f8fd6eccfca76ad523da2651ac46aa`.
- Promotion commit `e1b7dcf43338b8baa97c117493700b3dddbf0211` and paper-preflight
  commit `c3c3d702d1f8fd6eccfca76ad523da2651ac46aa` are authored as
  `bmendonca3` and pushed to both `main` and `v1-task-expansion`.

## Completion Gate

Complete for the current 54-task Sonnet public-split promotion. This does not
close the external-review, current tool-agent, private-holdout, or v1 release
gates.
