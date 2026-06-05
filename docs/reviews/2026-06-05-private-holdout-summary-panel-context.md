# Private Holdout Summary Panel Context

Date: 2026-06-05

Question:

Does the new private holdout summary workflow improve v0-candidate evidence
without leaking private task details or overclaiming final v0 readiness?

## Current Public Repo State

AuthZBench-SaaS remains alpha/pre-v0. The public split is unchanged:

- 6 public synthetic SaaS apps
- 44 public tasks
- 18 public vulnerable tasks
- 26 public secure controls
- 10 public authorized-allow controls

## Change Under Review

Tracked public changes:

- `scripts/summarize_holdout_pack.py`
- `tests/test_holdout_summary.py`
- `docs/holdout-and-contamination.md`
- `docs/v0-task-build-matrix.md`
- `README.md`
- `docs/status.md`
- `CHANGELOG.md`

The utility reads ignored private manifests and emits a count-level summary
only. It intentionally does not include private task IDs, seeds, route paths,
oracle bodies, private file paths, or raw diagnostics.

## Local Private Evidence

An ignored local 24-task private holdout pack now exists under the ignored
`tasks_private/holdout/` root. The private task bodies are intentionally not
included in this review packet and must not be committed.

Redacted local validation results:

- private manifest count: 24
- vulnerable private tasks: 12
- private controls: 12
- private denial controls: 6
- private authorized-allow controls: 6
- app coverage: 6 apps, 4 tasks per app
- route variants: 24
- decoy variants: 24
- `leaderboard_suitable`: true
- `rehearsal_manifest_count`: 0
- `public_structure_overlap_count`: 0
- Git-tracked private holdout manifest count: 0

Private maintainer replay check:

- private task count: 24
- passed via backend scoring/replay: 24
- failure count: 0

Strict v0 audit after the local private pack:

- `private_holdout_pack`: passed
- `task_mix`: passed
- total vulnerable tasks across public plus private: 30
- total controls across public plus private: 38
- total authorized-allow controls across public plus private: 16
- `v0_ready`: false

Remaining strict v0 blockers:

- baseline registry still has 0 current public model families
- repeated model baselines still missing
- tool-agent baseline still missing
- release-candidate leaderboard submission still missing
- most review sections are not marked v0-ready
- release evidence fields remain false

## Review Focus

Please check:

- whether the summary utility is genuinely public-safe
- whether docs avoid implying that the private pack is public or that v0 is done
- whether the README Docker-validation mismatch is fixed
- whether the tests are enough for this checkpoint
- whether any tracked file could leak private holdout task details, local paths,
  raw diagnostics, or generated private artifacts

Do not inspect, print, summarize, or quote private holdout task bodies.
Do not edit files. Do not mutate Git. No web is needed.
