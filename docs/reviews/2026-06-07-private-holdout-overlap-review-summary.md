# Private Holdout Overlap Validation Review Summary

Review date: 2026-06-07

Question: Does the private-pack validation reject structural reuse across
declared private holdout packs without weakening public-overlap checks, leaking
private task details, or implying that active and candidate packs already
exist?

## Review Runs

- Kiro `claude-opus-4.8`, high effort: read the relevant files but did not
  return a verdict within the bounded review window. The stale local process was
  stopped and this run is not counted.
- Kiro `claude-opus-4.6`, medium effort, correctness review: returned `CLEAN`
  after checking cross-pack comparison ordering, count-only error output,
  preservation of public-overlap validation, safe optional input handling, and
  focused test coverage.
- Kiro `claude-opus-4.6`, medium effort, goal-completeness review: returned
  `READY_TO_RECORD`, while requiring the actual active plus shadow/candidate
  private-pack implementation gate to remain open.
- Parent reviewer pass: found that the initial implementation counted matching
  manifests while labeling the result as a fingerprint count. The implementation
  was changed to count unique overlapping structural fingerprints, and the
  regression test now proves that duplicate matching manifests count once.
- Kiro `claude-opus-4.6`, medium effort, post-fix review: returned `CLEAN` and
  explicitly confirmed unique-count semantics, privacy, predecessor ordering,
  public-check regression safety, and the limited claim scope in `docs/goal.md`.

Raw Kiro output was retained in local ignored `/tmp` logs for the active work
session and is not committed. No reviewer was given permission to edit files,
execute repository commands, or print private manifest content.

## Accepted Result

- `scripts/validate_holdout_pack.py` accepts repeated
  `--comparison-private-task` inputs and rejects unique structural fingerprints
  shared with those comparison packs.
- `scripts/validate_v1_readiness.py` passes a snapshot of all previously
  declared private-pack patterns when validating each successive pack.
- Error and summary output report counts only. They do not emit private task
  IDs, seeds, routes, oracle strings, structural signatures, or manifest bodies.
- Existing public ID, seed, and structural-overlap validation remains active.
- Focused direct and integration tests cover private-to-private rejection,
  predecessor accumulation, and unique-fingerprint count semantics.

## Verification

- `python3 -m unittest discover -s tests -p 'test_holdout_validator.py'`
  passed: 10 tests.
- `python3 -m unittest discover -s tests -p 'test_v1_readiness_validator.py'`
  passed: 30 tests.
- `python3 -m unittest discover -s tests -p 'test_ci_workflow.py'` passed:
  2 tests.
- `python3 -m compileall -q scripts tests` passed.
- Direct validation of the ignored 24-task local pack passed with zero public
  and private structural overlaps.
- A negative control comparing that pack against itself failed as required and
  reported 24 unique private structural overlaps without task-level details.
- `python3 scripts/validate_public.py --include-scripted-baseline` passed,
  including 187 tests and the 54-task scripted baseline.

## Remaining Boundary

This review completes only the validation-mechanism subgate. It does not prove
that a release active pack and an independent shadow or candidate pack have
been authored, registered, fingerprinted, hosted, or used for eligible repeated
private evaluation. Those goal items remain open.
