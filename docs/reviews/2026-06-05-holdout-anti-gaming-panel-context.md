# Holdout Anti-Gaming Panel Context

Date: 2026-06-05

Section reviewed: holdout, contamination, and anti-gaming design.

## Review Question

Does the current holdout validation slice make AuthZBench-SaaS harder to game
without overclaiming that the public alpha/pre-v0 repository is leaderboard-ready?

## Changed Surface

- `scripts/validate_holdout_pack.py`
- `scripts/generate_holdout_rehearsal_pack.py`
- `tests/test_holdout_validator.py`
- `tests/test_holdout_rehearsal_generator.py`
- `docs/goal.md`
- `ROADMAP.md`
- `README.md`
- `docs/holdout-and-contamination.md`
- `docs/status.md`
- `docs/v0-release-plan.md`
- `docs/publish-checklist.md`
- `tasks_private/README.md`
- `CHANGELOG.md`

## Parent-Verified Facts

- The repository is still documented as alpha/pre-v0, not release v0.
- Real private holdout manifests are not in public Git history.
- `tasks_private/holdout/` and `docs/reviews/panel-logs/` are ignored.
- The rehearsal generator creates a local ignored workflow-test pack only.
- Rehearsal validation passes shape checks but returns
  `leaderboard_suitable: false`.
- The validator now requires non-empty private `route_variant` and
  `decoy_variant` metadata.
- The validator detects private manifests that reuse public task structural
  fingerprints, while allowing explicitly marked rehearsal manifests for
  workflow testing only.

## Verification Already Run

- `python3 -Wd -m unittest discover -s tests -p 'test_holdout_validator.py'`
- `python3 -Wd -m unittest discover -s tests -p 'test_holdout_rehearsal_generator.py'`
- `python3 -m compileall -q scripts tests`
- `git diff --check`
- `python3 scripts/generate_holdout_rehearsal_pack.py --force && python3 scripts/validate_holdout_pack.py`
- `python3 scripts/validate_public.py --include-scripted-baseline`

## Known Remaining v0 Gaps

- The public repo still does not include the real private holdout pack.
- Private holdout execution is not yet protected or hosted.
- Route-alias randomization and additional private decoy variation still need to
  be implemented in the real non-public holdout pack.
- Repeated real model/agent baselines are still incomplete.
- Final v0 release-readiness review has not been completed.

