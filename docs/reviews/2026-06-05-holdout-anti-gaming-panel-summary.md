# Holdout Anti-Gaming Panel Summary

Date: 2026-06-05

Section reviewed: holdout, contamination, and anti-gaming design.

## Reviewers

- Gemini 3.5 Flash (High): verified by panel runner log.
- Gemini 3.1 Pro (High): verified by panel runner log.
- Claude Sonnet 4.6 (Thinking): model label verified by panel runner log,
  but no usable final review content was returned.
- Claude Opus 4.6 (Thinking): model label verified by panel runner log,
  but no usable final review content was returned.
- panel reviewer: independent holdout audit reviewer.
- Parent reviewer: final synthesis and local verification.

Raw panel runner logs and outputs are intentionally ignored under
`docs/reviews/panel-logs/`.

## Findings

### Accepted And Fixed

1. `leaderboard_suitable: false` alone was too weak as a rehearsal marker.
   A renamed public task could set that flag and avoid the non-rehearsal
   structural-copy error. Fixed by requiring generator-style rehearsal markers:
   rehearsal note plus rehearsal ID and seed prefixes.

2. Exact structural fingerprints were too prose-sensitive. A public task with
   only `policy` or `objective` reworded could bypass the copy detector. Fixed
   by fingerprinting behavioral structure instead: app, vulnerability/control
   shape, expected boundary, oracle shape, and normalized control request shape.

3. Variant metadata needed to reject placeholders, not only missing keys. Fixed
   by requiring non-empty string values for `holdout_variant.route_variant` and
   `holdout_variant.decoy_variant`.

### Accepted As Remaining v0 Work

1. The validator checks declared route and decoy variants, but it does not prove
   those variants are implemented in target app route tables. That remains a
   real v0 private-holdout implementation gate.

2. The public rehearsal pack is intentionally a workflow test. It is not a real
   private holdout and must not be used for leaderboard scoring.

3. Protected private-holdout execution is still required before top-benchmark or
   leaderboard claims. Participants must not receive readable holdout manifests.

### Rejected

No panel findings were rejected.

## Verification After Fixes

- `python3 -Wd -m unittest discover -s tests -p 'test_holdout_validator.py'`
  passed with 9 tests.
- `python3 -Wd -m unittest discover -s tests -p 'test_holdout_rehearsal_generator.py'`
  passed with 3 tests.
- Independent second-pass audit ran
  `python3 -m unittest discover -s tests -p 'test_holdout*.py'` and passed with
  12 tests.
- `python3 -m compileall -q scripts tests` passed.
- `git diff --check` passed.
- `python3 scripts/generate_holdout_rehearsal_pack.py --force && python3 scripts/validate_holdout_pack.py`
  passed shape validation with `leaderboard_suitable: false`,
  `rehearsal_manifest_count: 24`, and `public_structure_overlap_count: 24`.
- `python3 scripts/validate_public.py --include-scripted-baseline` passed with
  54 tests, public manifest validation, compile checks, Docker Compose config,
  and 44/44 deterministic scripted baseline tasks.
- Private holdout JSON remains untracked; `tasks_private/holdout/` is ignored.

## Decision

This section is stronger and honest for alpha/pre-v0. It meaningfully reduces
the value of renamed public-task copies and placeholder holdout metadata, but it
does not make the benchmark v0, leaderboard-ready, or top-tier on its own. The
remaining v0 gates are real private holdouts, protected execution, route/decoy
implementation checks, repeated real model baselines, and final release
readiness review.

