# Artifact Index

Public-safe artifacts live under `artifact/`. Each tracked artifact is scoped
to a specific claim boundary. Do not present any artifact here as proof
beyond its own boundary.

## Release Evidence

- `v1-release-candidate-validation.json`: v1 release-candidate evidence
  pinned to the CI-validated commit, the `v1.0-internal` tag, the benchmark
  source SHA, and the active private pack fingerprint. Carries an explicit
  `public_claim_boundary` and `external_review_status: deferred_to_v2`.
  Allowed claim: v1 release-candidate evidence under the internal/non-external
  release definition. Not a claim of external acceptance.
- `v1-release-candidate-validation.template.json`: template for future
  release-candidate evidence.
- `v1-release-candidate-validation-runbook.json`: runbook describing how the
  v1 release-candidate evidence is collected. Not evidence itself.
- `v1-readiness-public-view.json` (under `expected-output/`): public-view
  v1 readiness fixture. `v1_ready: true` is scoped to the internal/public-view
  readiness gates only. Allowed claim: public-view readiness gates pass. Not
  a claim of external acceptance.
- `release-evidence.json` (under `docs/`): tracked release evidence registry.
- `v1-paper-readiness.json` (under `docs/`) and
  `v1-paper-readiness-runbook.json`: paper-scaffold readiness evidence and
  the runbook that describes it.

## Task Quality

- `task-quality-gate-contract.json`: public-safe acceptance contract for
  task-quality gates enforced during public validation. Allowed claim:
  contract exists and is machine-checkable. Not a claim of external task
  review.

## Harbor Adapter

- `harbor-adapter-contract.json`: public-safe machine-readable contract for
  the Harbor-compatible adapter target. Allowed claim: the adapter target is
  specified. Not a claim of Harbor execution, parity, or acceptance.
- `harbor-adapter-readiness-blockers.json`: blocker record for missing
  adapter metadata, parity, local execution, and adapter review evidence.
- `harbor-adapter-metadata.template.json`: template for future real
  Harbor adapter metadata.
- `harbor-parity-experiment.json`: tracked parity experiment evidence
  (historical aggregate-means; new evidence uses per-task pairing via
  `scripts/run_harbor_parity_experiment.py` and `evidence_status: current`).
  Allowed claim: parity evidence exists for the generated public skeleton.
  Not a claim of Harbor execution or platform acceptance.
- `harbor-parity-experiment.template.json`: template for future per-task
  pairing evidence.
- `harbor-adapter-smoke.json`: local adapter smoke evidence summary.
- `harbor-local-execution-smoke.json`: local Harbor execution preflight
  summary (records whether the Harbor CLI is on `PATH`; in a checkout
  without Harbor, the gate is recorded as blocked on the missing CLI).
- `harbor-dataset-public-smoke/`: redacted generated dataset artifacts for
  the public smoke path.

## Hosted Submission And Submission Smoke

- `hosted-submission-execution-runbook.json`: public-safe runbook for the
  maintainer-hosted or fully containerized release-candidate smoke path.
  Not hosted execution evidence.
- `submission-runner-smoke.json`: tracked release-candidate
  hosted/containerized smoke evidence.
- `submission-runner-smoke.template.json`: template for future smoke
  evidence.

## Private Holdouts

- `private-holdout-active-public-summary.json`: redacted aggregate summary
  for the active private pack.
- `private-holdout-shadow-public-summary.json`: redacted aggregate summary
  for the shadow/candidate private pack.
- `private-holdout-rotation-metadata.template.json`: template for
  maintainer-only rotation metadata.
- `private-holdout-operation-runbook.json`: runbook for operating active
  plus shadow/candidate private packs.
- `private-holdout-operation-blocker.json`: blocker record for items the
  v1 internal holdout operation does not yet satisfy.

## v1 Task Scale And Reporting

- `v1-task-scale-roadmap.json`: public-safe planning roadmap for v1
  task scale. Not task-scale evidence.

## Public Validation

- `run-public-validation.sh`: bounded public validation entrypoint. See
  [`docs/validation-commands.md`](validation-commands.md) for the full set.
- `expected-output/`: public-safe expected outputs for stable validation
  signals.

## Boundaries Common To All Artifacts

- No artifact here contains private holdout bodies, seeds, routes, oracle
  fields, or raw private result bundles.
- Raw `harbor-jobs/`, `results/`, `captures/`, `docs/reviews/panel-logs/`,
  `tasks_private/holdout/`, `.harbor/`, and `.handoff/` paths are ignored
  and must not appear in tracked Git.
- Each artifact's own `public_claim_boundary` (when present) is authoritative
  for that artifact.
