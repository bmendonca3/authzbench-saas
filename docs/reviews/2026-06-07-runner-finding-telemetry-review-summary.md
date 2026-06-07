# Runner Finding Telemetry Review Summary

Review date: 2026-06-07

Status: completed internal review of the finding-total semantics used by public
and protected benchmark summaries. This is not one of the three required
external v1 review lanes.

## Question

Can a summary distinguish findings parsed and scored from the submitted
`submission.json` file from optional self-reported tool-probe telemetry without
changing historical scoring behavior?

## Accepted Change

- `scored_submission_finding_total` sums the scorer-derived per-task
  `submission_finding_count`.
- `submitted_finding_total` retains its existing meaning: optional adapter
  telemetry summed from `tool-probes.json`.
- Both the public runner and protected private evaluator emit the new
  scorer-derived field.
- The redacted private summary preserves the aggregate count without exposing
  task identities, routes, seeds, or oracle data.
- Existing fields and scoring behavior remain unchanged.

## Review Evidence

- Kiro `claude-opus-4.6`, medium-effort read-only audit, returned `CLEAN` for
  the initial public-runner implementation and its tests. It confirmed the two
  totals had distinct sources, names, and backward-compatible semantics.
- Parent review found one cross-path consistency gap: the protected private
  evaluator still emitted only the adapter-derived total. The implementation
  was expanded to cover that path and its redacted summary.
- Kiro `claude-opus-4.8`, high-effort post-fix audit, returned `NEEDS_FIXES`.
  It found no computation, compatibility, or privacy defect, but correctly
  identified that the protected evaluator lacked an end-to-end divergent-total
  test and that the registry completion wording was premature.
- The protected evaluator now has an end-to-end test where the scorer counts one
  submitted finding while adapter telemetry reports two. The test also checks
  the redacted aggregate and absence of the private task ID.
- The legacy `submitted_finding_total` name remains for backward compatibility.
  Schema and bundle documentation explicitly identify it as optional adapter
  telemetry wherever the two totals are surfaced.
- The replacement Kiro audit returned `CLEAN` for the two finding-total fields,
  but its analysis exposed a pre-existing protected-run metric mismatch:
  protected `false_positive_rate` counted only controls with submitted findings,
  while the public runner and leaderboard validator count all failed secure
  controls. Parent review accepted the observation and aligned the protected
  path with the shared metric contract.
- A protected-run regression test now proves that a failed backend control with
  no submitted finding yields `false_positive_rate: 1.0` and
  `control_false_report_rate: 0.0`, matching the public runner.
- Kiro `claude-opus-4.6`, medium-effort final audit, returned `CLEAN` after
  checking both runners, divergent-total tests, redaction privacy, metric
  alignment, schema documentation, bundle guidance, and registry wording.

Raw Kiro output remains in ignored local `/tmp` evidence and is not committed.

## Verification Gate

Completed evidence:

- 9 focused public-runner tests passed.
- 7 focused protected-evaluator tests passed.
- the full 192-test unit suite passed.
- `python3 scripts/validate_public.py --include-scripted-baseline` passed,
  including the current 54-task scripted baseline.
- the final replacement Kiro verdict was `CLEAN`.
- parent-level diff and metric-contract review found no remaining actionable
  issue.
