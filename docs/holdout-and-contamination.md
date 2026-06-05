# Holdout And Contamination Plan

AuthZBench-SaaS should avoid the failure mode where public task details become
memorized by frontier models or agent harnesses.

## Current Protection

The current scaffold derives tenant IDs, object IDs, org IDs, invoice IDs, and
actor tokens from each task seed. This prevents static ID memorization but does
not fully protect route or vulnerability-location memorization.

## Public Split

Use the existing `tasks/*/*.json` manifests as the public development split.
This split is useful for:

- harness integration
- local smoke tests
- baseline debugging
- public methodology review

## Private Holdout Split

Create a private holdout split before any public leaderboard claim. The public
repository documents the mechanism, but private holdout manifests should live
outside the public Git history. They should use the same schema but should not
publish:

- exact route paths
- exact vulnerability locations
- scorer oracle subsets
- reference exploits
- task seeds

The real v0 holdout should contain 20-30 unpublished tasks. The minimum useful
v0 holdout target is 24 tasks:

- 8 BOLA or tenant/object-boundary tasks
- 8 BFLA, invite/membership, token-scope, or role-boundary tasks
- 8 secure controls, including denial controls and authorized-allow controls

The public repo intentionally does not include holdout JSON. Maintainers can keep
local manifests under `tasks_private/holdout/`; that path is ignored by Git.
Those local files prove the private split mechanism during development but do
not satisfy the final holdout size target unless a separate private pack contains
at least 20 tasks, with 24 preferred for balanced coverage.

## Holdout Execution Model

Private holdouts should not be handed to participants as readable local JSON.
For serious leaderboard use, prefer one of these execution models:

- hosted scorer API that renders tasks, runs targets, records server-side
  request logs, and returns only aggregate results
- maintainer-run private evaluation where submitted agent harnesses run in an
  isolated container and receive only rendered contexts
- encrypted/local package only for trusted internal validation, not public
  leaderboard claims

## Future Randomization

Add procedural randomization for:

- route aliases, such as `/api/tasks/<id>` versus `/api/work-items/<id>`
- role names, while preserving role semantics
- resource names and response field order
- harmless decoy endpoints
- multiple seeds per task

## Release Discipline

- Publish public split results separately from private leaderboard results.
- Version every benchmark release.
- Keep a change log for added, removed, or modified tasks.
- Re-run baseline agents after every scorer or task change.
