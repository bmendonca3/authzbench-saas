# Leaderboard Artifact Validation Panel Summary

Date: 2026-06-05

Section: baseline methodology and leaderboard schema.

## Reviewers Counted

- panel implementation reviewer
- internal read-only auditor
- Gemini 3.5 Flash (High), verified from panel runner log
- Gemini 3.1 Pro (High), verified from panel runner log

Claude Sonnet 4.6 (Thinking) and Claude Opus 4.6 (Thinking) labels were
verified in panel runner logs, but their outputs were empty for this run, so they
were not counted as content reviewers.

Raw panel runner logs are intentionally ignored under `docs/reviews/panel-logs/`.

## Accepted Findings

1. Eligible rows could pass without a source artifact unless callers remembered
   `--require-source-summary`.

   Disposition: fixed. `leaderboard_eligible: true` now requires
   `source_run_summary` regardless of the CLI flag. The CLI flag remains useful
   for requiring source summaries on non-eligible tracked examples.

2. Task-row recomputation could crash on malformed numeric fields such as
   `target_request_count`, `submission_finding_count`, or `score`.

   Disposition: fixed. Recompute logic now validates task-row numeric fields and
   reports structured errors instead of raising `ValueError` or `TypeError`.

3. Eligible submissions could theoretically omit secure controls and claim a
   clean false-positive rate from a vulnerability-only subset.

   Disposition: fixed. `leaderboard_eligible: true` now requires both vulnerable
   tasks and secure controls.

## Verification After Fixes

```bash
python3 -Wd -m unittest discover -s tests -p 'test_leaderboard_submission.py'
python3 scripts/validate_leaderboard_submission.py --submission 'examples/leaderboard/*.json' --require-source-summary
```

Both passed after the accepted findings were fixed.

## Remaining Release Risks

- The tracked scripted source summary is an alpha aggregate artifact without
  `run_id`; it is acceptable as non-eligible public evidence but not sufficient
  for v0 leaderboard identity proof.
- Real private holdout bundles, protected execution, repeated current real model
  baselines, and a current tool-agent baseline are still required before v0.
- This section is acceptable for the alpha/pre-v0 checkpoint, not for a final
  leaderboard release by itself.
