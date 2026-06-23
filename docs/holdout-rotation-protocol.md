> [!NOTE]
> **Consolidation Notice**: This file is slated for consolidation. Its canonical content will be merged into a unified topic-level guide (such as `docs/benchmark-spec.md` or `docs/scoring-and-submissions.md`) in subsequent consolidation phases.

# Holdout Rotation Protocol

This protocol defines how private holdout packs should evolve after the first
release without leaking task details or mixing incompatible scores.

## Purpose

Private holdouts should test current agent capability, not memorization of old
public or leaked task structure. A mature benchmark should therefore use
versioned private packs with clear retirement and compatibility rules.

## Pack States

This protocol governs maintainer-private scoring governance and
leaderboard-candidate rows inside the repo evidence model. It is not hosted leaderboard operation, not platform acceptance, and not third-party submissions; those remain v2-deferred tracks.

- `candidate`: internally built and validated, not yet used for
  maintainer-private scoring governance
- `active`: current private pack for maintainer-private scoring governance and
  leaderboard-candidate rows
- `shadow`: run alongside the active pack to detect drift or leakage, but not
  used for leaderboard-candidate rows yet
- `retired`: no longer used for leaderboard-candidate rows; kept only for
  historical reproducibility
- `invalidated`: removed from scoring because leakage, task flaw, or scorer
  error made results unreliable

## Rotation Cadence

For v1-scale use, maintainers should prepare at least two private packs:

- one active pack for current scoring
- one shadow pack for future rotation and drift checks

The ignored `tasks_private/holdout/rotation-metadata.json` file must declare
each pack's ID, role, safe relative path, concrete version label, and lowercase
SHA-256 fingerprint. The v1 readiness validator recomputes each pack
fingerprint from the private manifests and requires every declared fingerprint
to match before the rotation gate can pass.

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

Pack summaries may publish counts, roles, versions, and fingerprints only.
They must not publish task IDs, seeds, routes, oracle bodies, exploit hints,
private context text, raw private bundles, private logs, or local paths.

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

Rotation metadata must also include a concrete compatibility object, concrete
retirement triggers, and a rerun policy. Current-comparison readiness requires
rerunning both no-tools and tool-agent baselines, and old rows must be retained
only as `legacy_snapshot` or `deprecated`.

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

This protocol supports maintainer-private scoring governance credibility, but
it does not replace external task review or protected execution. Public-safe
claim wording is enforced by `python3 scripts/check_claim_boundary.py`.
