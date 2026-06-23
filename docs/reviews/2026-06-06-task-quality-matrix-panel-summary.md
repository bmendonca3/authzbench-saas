# Task Quality Matrix Panel Summary

Date: 2026-06-06

Scope: generated public-safe task-quality matrix, generator, validation gate,
targeted tests, and README/docs references.

## Counted Reviewers

- Gemini 3.5 Flash (High), verified by the panel runner CLI log
- Gemini 3.1 Pro (High), verified by the panel runner CLI log
- Kiro CLI `claude-opus-4.8`, verified by live model catalog and Kiro output
- panel reviewer

Claude Sonnet 4.6 and Claude Opus 4.6 panel runner labels were verified by logs
but did not return substantive review text for this checkpoint, so they are not
counted as substantive reviewers.

Raw prompts and logs are kept under ignored `docs/reviews/panel-logs/` and are
not part of the public release artifact.

## Consensus

Reviewers agreed that the matrix improves benchmark credibility by making the
public task split easier to audit:

- it summarizes the 46 public tasks by app, vulnerable/control mix, control
  type, boundary keys, and explicit workflow evidence requirements
- it is generated from tracked public task manifests instead of hand-written
  prose
- public validation regenerates it and fails on drift
- docs frame it as a structural audit aid, not a leaderboard, v0, or v1 claim

## Accepted Findings

1. New matrix files must be tracked before drift checks and privacy scans are
   meaningful.

Disposition: accepted. The generated matrix files, generator, and tests are part
of this public checkpoint.

2. Whole-matrix privacy assertions should cover future fields, not only the
   first multi-step task.

Disposition: accepted. The matrix tests now scan all public task manifests for
sensitive seeds, path templates, ref templates, and high-signal oracle/body
literals that must not appear in the generated matrix.

3. Raw control status values and evidence-step names were more detailed than
   needed for a public structural matrix.

Disposition: accepted. The generator now publishes aggregate control status
check counts and evidence-step structure only. It omits evidence-step names,
request paths, request bodies, oracle bodies, and seeds.

4. `schema_version` could be confused with benchmark `v1` readiness.

Disposition: accepted. The matrix schema label is now
`task-quality-matrix-schema-1`, which avoids a benchmark-version signal.

## Claim Boundary

This checkpoint supports a narrower claim: the public task scaffold is more
reviewable and harder to overstate because task-quality evidence is generated
and validated. It does not prove:

- leaderboard readiness
- v0 or v1 release readiness
- private-holdout quality
- strong multi-step coverage beyond the current first workflow task

## Verification

Required verification for this checkpoint:

- `python3 scripts/generate_task_quality_matrix.py`
- `python3 -Wd -m unittest discover -s tests -p 'test_task_quality_matrix.py'`
- `python3 -Wd -m unittest discover -s tests -p 'test_validate_public.py'`
- full public validation
- release audit in allow-incomplete mode
- privacy check proving raw panel logs, private holdouts, results, and captures
  are untracked
- remote CI after commit
