# Leaderboard Schema v1 Panel Summary

Section: baseline methodology, leaderboard schema, and private execution trust
boundary.

Disposition: accepted for the stable schema checkpoint. Overall v0 readiness
remains intentionally reopened until fresh protected runs restore an eligible
private row.

## Reviewers

- Gemini 3.5 Flash (High): verified model label; accepted after one empty-slice
  rate consistency fix and identified the workspace-only isolation limitation.
- Gemini 3.1 Pro (High): verified model label; accepted the schema and historical
  row demotion.
- Claude Sonnet 4.6 (Thinking): verified label, empty output; not counted for
  substantive findings.
- Claude Opus 4.6 (Thinking): verified label, empty output; not counted for
  substantive findings.
- Kiro `claude-opus-4.8`: verified from the live Kiro model catalog; accepted
  schema completion while requiring an eligible-ready runner-to-row workflow.
- ChatGPT reviewer: parent review plus an independent Codex subagent review.

Raw panel logs remain untracked under `docs/reviews/panel-logs/`.

## Accepted Findings

1. Comparability keys originally omitted benchmark version and commit.
   Fixed: both are now part of the deterministic key.
2. Repeat evidence originally accepted asserted run IDs and variance.
   Fixed: eligible rows require one source summary per run, matching execution
   contracts, exact run-ID coverage, and recomputed population standard
   deviation.
3. A `runner-emitted` string alone was weak provenance.
   Fixed: protected summaries now include a deterministic integrity envelope.
   The docs explicitly state that this is not a cryptographic signature.
4. Empty-slice rates differed between runner and validator.
   Fixed: both use `null` when a rate has no denominator.
5. Temporary empty workspaces did not prevent absolute host-path reads.
   Fixed for the current macOS maintainer path: `sandbox-exec` denies reads of
   private holdouts, raw results, captures, and raw panel logs. Eligible private
   sources require host private-path denial.
6. Fresh protected summaries did not have a tested route into a repeated row.
   Fixed: `scripts/build_leaderboard_submission.py` and its end-to-end test
   exercise runner-style redacted summaries through eligibility validation.

## Historical Row

The Haiku private row remains schema-valid but non-eligible. Its task
fingerprint was reconstructed after execution and its two source runs used
different commits. It is retained as transparent historical pipeline evidence,
not current ranking evidence.

## Verification

Targeted checks passed for:

- leaderboard validation
- protected private execution, including host-path denial
- protected evidence validation
- runner summaries
- v0 release-gate behavior
- repeated-summary leaderboard building

The strict v0 gate is expected to remain red until fresh same-commit,
host-isolated private runs produce an eligible row and release evidence is
refreshed.
