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

Maintainers can validate an ignored local pack with:

```bash
python3 scripts/validate_holdout_pack.py
```

For release evidence or internal review packets, maintainers can emit a
public-safe count summary without exposing private task bodies:

```bash
python3 scripts/summarize_holdout_pack.py \
  --output docs/private-holdout-summary.redacted.example.json
```

Only publish a summary when it is count-level and redacted. It must not include
task IDs, seeds, route paths, oracle bodies, private diagnostics, raw run
artifacts, or local file paths. The summary is useful as supporting evidence
that an ignored private pack exists and passes shape checks; it is not a
substitute for protected private execution.

Redacted protected-execution summaries can be checked with:

```bash
python3 scripts/validate_protected_private_evidence.py \
  --summary 'docs/protected-private*-2026-06-05.redacted.json'
```

That validator requires repeated redacted private-holdout runs, unique run IDs,
consistent private-holdout counts, no tracked private manifests, no tracked raw
private result bundles, rendered-context-only agent execution, zero invalid
submissions, zero secure-control false reports, and at least one protected
tool-agent summary with target-request coverage. It rejects task rows, raw
transcripts, target-log paths, local result paths, private manifest paths, and
other non-redacted evidence.

They can also generate an ignored local rehearsal pack to verify the private
pack workflow end to end:

```bash
python3 scripts/generate_holdout_rehearsal_pack.py --force
python3 scripts/validate_holdout_pack.py
```

The rehearsal pack is generated from public task structure, so it is only a
workflow test. It must not be used for private leaderboard scoring, model
ranking, or a `v0` release claim.

The validator checks the normal task schema, requires `split=private_holdout`,
rejects public seed prefixes, rejects public task ID and seed reuse, requires
coverage across all six app families, limits over-concentration in one app,
enforces denial-control and authorized-allow-control minimums, requires
non-empty private-only route and decoy variant metadata, and rejects
non-rehearsal manifests that reuse public task structural fingerprints. A
manifest is treated as rehearsal only when it carries the generator-style
rehearsal note plus rehearsal ID and seed prefixes. When rehearsal manifests or
public-structure fingerprints are present, the validator reports warnings and
sets `leaderboard_suitable: false`.

The redacted summary utility wraps the same validator and reports only:

- total manifest, vulnerable, control, denial-control, and authorized-allow
  counts
- app coverage, max tasks per app, route-variant count, and decoy-variant count
- whether rehearsal manifests or public structural fingerprints were present
- whether any private holdout manifests are tracked by Git
- counts of validation errors and warnings, not the private diagnostics

Default v0-shape validation requires:

- 20-30 private tasks, with 24 preferred
- a minimum of twelve vulnerability-bearing tasks
- at least 8 secure controls
- at least 6 covered apps
- no more than 8 tasks in a single app family
- at least 4 denial controls
- at least 4 authorized-allow controls
- at least 6 non-empty route variants declared through private
  `holdout_variant` metadata
- at least 6 non-empty decoy variants declared through private
  `holdout_variant` metadata
- no non-rehearsal public task structural copies

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
