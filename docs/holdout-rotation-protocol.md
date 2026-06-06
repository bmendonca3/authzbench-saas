# Holdout Rotation Protocol

This protocol defines how private holdout packs should evolve after the first
release without leaking task details or mixing incompatible scores.

## Purpose

Private holdouts should test current agent capability, not memorization of old
public or leaked task structure. A mature benchmark should therefore use
versioned private packs with clear retirement and compatibility rules.

## Pack States

- `candidate`: internally built and validated, not yet used for leaderboard
  scoring
- `active`: current private pack for release-facing leaderboard evaluation
- `shadow`: run alongside the active pack to detect drift or leakage, but not
  used for public ranking yet
- `retired`: no longer used for current rankings; kept only for historical
  reproducibility
- `invalidated`: removed from scoring because leakage, task flaw, or scorer
  error made results unreliable

## Rotation Cadence

For v1-scale use, maintainers should prepare at least two private packs:

- one active pack for current scoring
- one shadow pack for future rotation and drift checks

Rotate when any of these happen:

- a major release changes public task families or scorer semantics
- private task leakage is suspected
- agents begin to overfit a narrow task family
- the active pack is older than two major benchmark cycles
- external review identifies a material task-quality issue

## Pack Balance

Each active pack should preserve the benchmark's core distribution:

- all six app families represented
- vulnerable and secure-control tasks both present
- denial controls and authorized-allow controls both present
- BOLA, BFLA, membership, token-scope, sharing, and admin/settings boundaries
  represented across the pack
- no app family or boundary type dominates the score

Pack summaries may publish counts and coverage only. They must not publish task
IDs, seeds, routes, oracle bodies, exploit hints, private context text, private
logs, or local paths.

## Compatibility

Scores from different private packs should not be merged unless the packs are
declared compatible in a release note. When a pack rotates:

- mark old leaderboard rows as `legacy_snapshot`
- label new rows with the active pack version
- rerun core baselines on the new pack before comparing agents
- keep public-split development results separate from private leaderboard
  results

If a scorer bug affects a private pack, mark affected rows as `deprecated` and
publish a short non-sensitive explanation.

## Leakage Response

When leakage is suspected:

1. Stop accepting new release-facing rows for the affected pack.
2. Move the pack to `invalidated` or `retired`.
3. Build a replacement candidate pack with different seeds, routes, decoys, and
   task structure.
4. Run baseline agents again before reopening current rankings.
5. Publish only redacted count-level evidence about the rotation.

## Release Evidence

Before a private pack is used for leaderboard claims, maintainers should have:

- passing `scripts/validate_holdout_pack.py` output
- redacted count-level summary
- protected execution evidence
- at least one no-tools baseline row
- at least one tool-agent baseline row with target-request coverage
- privacy check proving private manifests, raw result bundles, and panel logs
  are untracked

This protocol supports leaderboard credibility, but it does not replace external
task review or protected execution.
