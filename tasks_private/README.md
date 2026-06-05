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
