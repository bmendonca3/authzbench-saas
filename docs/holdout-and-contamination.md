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

The holdout should contain at least:

- 4 BOLA tasks
- 4 BFLA tasks
- 4 secure controls

The public repo intentionally does not include holdout JSON. Maintainers can keep
local manifests under `tasks_private/holdout/`; that path is ignored by Git.
Those local files prove the private split mechanism during development but do
not satisfy the final holdout size target unless a separate private pack contains
at least 12 tasks.

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
