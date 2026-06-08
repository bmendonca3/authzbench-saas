# Current 54-Task Claude Opus Evidence Review Summary

Status: promotion gate complete. This is internal review evidence, not one of
the three required external v1 review lanes.

## Scope

The review covers both current 54-task `claude-opus-4.6` no-tools summaries,
raw-to-promoted fidelity, active-fingerprint provenance, retained task
artifacts, registry counts, chart and readiness fixture updates, paper/report
wording, and current/stale claim boundaries.

## Raw Evidence

- Run `20260608T010424615768Z-6ce73f0b`: 54 tasks, 33 passed,
  `mean_score: 0.8444`, 14/21 exploit-proven vulnerable tasks, zero boundary
  reasoning, zero vulnerable full passes, `false_positive_rate: 0.0`, zero
  invalid submissions, and 21 scorer-counted findings.
- Run `20260608T011105635536Z-ae586ffd`: 54 tasks, 33 passed,
  `mean_score: 0.8444`, 14/21 exploit-proven vulnerable tasks, zero boundary
  reasoning, zero vulnerable full passes, `false_positive_rate: 0.0`, zero
  invalid submissions, and 21 scorer-counted findings.
- Both runs use benchmark commit
  `56fcbde7b54d05f3bc4da3813c5ecffb14320a35` and task-set fingerprint
  `f8d19cb89d347d1397f85bf978e6b7b232e8a2f1307fc2ac6ba02674e5c23c9f`.
- Both runs contain 54 task directories and 54 each of `context.json`,
  `submission.json`, `score.json`, `transcript.json`, and `model-output.json`.

## Interpretation

The Claude Opus 4.6 pair closes the current 54-task no-tools rerun gate for the
five public model families. It is diagnostic public-split evidence only. It
does not close the current live HTTP tool-agent gate, private-holdout evidence
gates, hosted/containerized release evidence, external-review lanes, 100+ task
scale, or v1 release readiness.

## Independent Audit

- Kiro Claude Opus 4.8 independently reconciled raw summaries, promoted
  summaries, run IDs, active fingerprint, retained artifacts, zero-failure
  diagnostics, registry counts, tests, chart data, and the public readiness
  fixture. It returned `VERDICT: CLEAN`.
- Kiro Claude Opus 4.8 independently audited docs, paper text, expected public
  readiness output, registry scope, and stale/current claim boundaries. It first
  returned `VERDICT: FINDINGS` for stale four-family and Opus-pending language.
  Those findings were fixed.
- A final narrow Kiro Claude Opus 4.8 claims re-audit verified that current
  docs say five no-tools families, Opus is no longer presented as pending,
  variance notes expect five current model families, the IEEE paper includes an
  Opus current-family paragraph, and the live HTTP tool-agent and v1 gates
  remain open. It returned `VERDICT: CLEAN`.

## Local Verification

- Parent artifact census confirmed 54/54 retained task artifacts for both raw
  runs, including context, submission, score, transcript, and model-output
  files.
- Parent model-output census found zero nonzero Kiro return codes, zero parse
  errors, zero missing submissions, and zero outer runner failures.
- `python3 -m unittest discover -s tests`: 196 tests passed.
- `python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view
  --expected-output artifact/expected-output/v1-readiness-public-view.json`
  passed and reports `current_public_model_family_count=5` with only the
  current public tool-agent baseline missing from the stable public evidence
  gate.
- `python3 scripts/validate_baseline_registry.py` passed with
  `baseline_count: 29`, `current_public_model_family_count: 5`, and
  `has_current_public_tool_agent_baseline: false`.
- `python3 scripts/validate_leaderboard_submission.py --submission
  'leaderboard_submissions/**/*.json' --require-source-summary` passed.
- `python3 scripts/generate_benchmark_charts.py` and
  `python3 scripts/generate_paper_tables.py` were rerun.
- `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` produced the
  IEEE paper PDF. Existing underfull-box and Tectonic bibliography rerun
  warnings remain nonblocking.

## Completion Gate

Complete for the current 54-task Claude Opus 4.6 public-split promotion. This
does not complete the broader `docs/goal.md` objective because live HTTP
tool-agent evidence, external review, private-holdout operation, hosted
execution, 100+ task scale, and strict release-candidate validation remain open.
