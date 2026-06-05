# Private Holdout Tasks

This directory documents the private holdout mechanism without publishing private
holdout manifests.

Do not commit private holdout task manifests here. The `.gitignore` excludes
`tasks_private/holdout/` so maintainers can keep local holdout manifests without
leaking exact routes, seeds, vulnerability locations, or scorer oracle details
into a public release.

The public repository should contain:

- this README
- optional schema documentation or redacted templates
- no private task JSON

Before serious public leaderboard claims, maintain a separate private holdout
pack with 20-30 private tasks, with 24 preferred for balanced coverage, as
described in `docs/holdout-and-contamination.md`.

Local validation command:

```bash
python3 scripts/validate_holdout_pack.py
```

The validator checks schema, `split=private_holdout`, non-public seeds, public
task ID/seed overlap, app-family coverage, per-app concentration, denial plus
authorized-allow control minimums, non-empty private route/decoy variant
metadata, and public task structural-copy overlap.

Maintainers can create a local ignored rehearsal pack with:

```bash
python3 scripts/generate_holdout_rehearsal_pack.py --force
```

That rehearsal pack is generated from public task structure and exists only to
test the private-pack workflow. It is not a real private leaderboard holdout and
should not be used for v0 scoring claims.
Generated rehearsal manifests include `leaderboard_suitable: false`, and the
holdout validator reports a warning when rehearsal manifests are present.
