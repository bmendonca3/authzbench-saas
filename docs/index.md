# Documentation Index

A reviewer who only has two minutes should be able to use this page to find
the right file without opening the full repository.

## Start Here

- [`README.md`](../README.md): project overview, current status, and claim
  boundaries.
- [`docs/benchmark-card.md`](benchmark-card.md): benchmark scope, intended
  use, and known limits.
- [`docs/evidence-and-claims.md`](evidence-and-claims.md): current claim
  ledger and approved public framing.
- [`docs/host-review-package.md`](host-review-package.md): Kaggle-like host
  review entrypoint, package map, and non-claim boundary.
- [`docs/kaggle-presentation-todo.md`](kaggle-presentation-todo.md):
  presentation checklist and remaining host decisions.

## Release Evidence

- [`docs/releases/v1.0-internal.md`](releases/v1.0-internal.md): v1.0-internal
  release note (status, included, not claimed, deferred to v2).
- [`docs/release-notes-v0.0.md`](release-notes-v0.0.md): v0.0 release note.
- [`artifact/v1-release-candidate-validation.json`](../artifact/v1-release-candidate-validation.json):
  v1 release-candidate evidence with explicit claim boundary.
- [`artifact/expected-output/v1-readiness-public-view.json`](../artifact/expected-output/v1-readiness-public-view.json):
  public-view v1 readiness fixture. `v1_ready: true` here is scoped to the
  internal/public-view readiness gates only; it does not claim external
  acceptance.
- [`docs/release-evidence.json`](release-evidence.json): tracked release
  evidence registry (v0.0 schema; the v1 strict release-evidence file lives
  outside public Git per the completion gate in [`docs/goal.md`](goal.md)).

## Task Quality

- [`docs/task-quality-rubric.md`](task-quality-rubric.md): task-quality review
  rubric.
- [`docs/task-quality-matrix.md`](task-quality-matrix.md): generated public
  task-quality matrix (audit aid, not a leaderboard claim).
- [`artifact/task-quality-gate-contract.json`](../artifact/task-quality-gate-contract.json):
  public-safe acceptance contract for task-quality gates.
- [`scripts/validate_task_quality_gate.py`](../scripts/validate_task_quality_gate.py):
  validator that enforces the contract.

## Harbor Adapter

- [`docs/harbor-integration-runbook.md`](harbor-integration-runbook.md):
  Harbor adapter target, parity methodology, and non-evidence boundary.
- [`artifact/harbor-adapter-contract.json`](../artifact/harbor-adapter-contract.json):
  public-safe machine-readable adapter contract.
- [`artifact/harbor-parity-experiment.json`](../artifact/harbor-parity-experiment.json):
  tracked parity experiment evidence (historical aggregate-means; new evidence
  uses per-task pairing).
- [`artifact/harbor-parity-experiment.template.json`](../artifact/harbor-parity-experiment.template.json):
  template for future per-task pairing evidence.
- [`artifact/harbor-adapter-readiness-blockers.json`](../artifact/harbor-adapter-readiness-blockers.json):
  blocker record for missing adapter, parity, and execution evidence.
- [`artifact/harbor-adapter-metadata.template.json`](../artifact/harbor-adapter-metadata.template.json):
  template for future real adapter metadata.
- [`artifact/harbor-adapter-smoke.json`](../artifact/harbor-adapter-smoke.json):
  local smoke evidence summary.
- [`authzbench_harbor/`](../authzbench_harbor/): repo-side Python package
  wrapping the skeleton builder, scorer bridge, redaction, and CLI.

## Private Holdouts

- [`docs/holdout-and-contamination.md`](holdout-and-contamination.md):
  holdout separation and contamination controls.
- [`docs/holdout-rotation-protocol.md`](holdout-rotation-protocol.md):
  rotating private holdout pack protocol.
- [`artifact/private-holdout-active-public-summary.json`](../artifact/private-holdout-active-public-summary.json):
  redacted aggregate summary for the active private pack.
- [`artifact/private-holdout-shadow-public-summary.json`](../artifact/private-holdout-shadow-public-summary.json):
  redacted aggregate summary for the shadow/candidate private pack.
- [`artifact/private-holdout-rotation-metadata.template.json`](../artifact/private-holdout-rotation-metadata.template.json):
  template for maintainer-only rotation metadata.

## Validation Commands

See [`docs/validation-commands.md`](validation-commands.md) for the bounded
public validation set, the maintainer-only strict set, and the privacy check
that should print nothing for a public commit.

## Artifact Packet

See [`docs/artifact-index.md`](artifact-index.md) for the public-safe
artifact index and what each tracked artifact is allowed to prove.

## External Validation / v2

- [`docs/v2-external-validation-roadmap.md`](v2-external-validation-roadmap.md):
  v2 validation lanes, deferred from v1.
- [`docs/v1-community-submission-governance.md`](v1-community-submission-governance.md):
  submission governance specification (not a live submission pipeline claim).

## Kaggle-Like Host Review

- [`docs/host-review-package.md`](host-review-package.md): one-page host review route and artifact map.
- [`docs/host-facing-one-page-summary.md`](host-facing-one-page-summary.md): host-facing one-page summary.
- [`docs/kaggle-presentation-todo.md`](kaggle-presentation-todo.md): concrete host-presentation checklist status.
- [`docs/kaggle-hosting-model.md`](kaggle-hosting-model.md): hosting models and proposed host-review path.
- [`docs/evaluation-for-hosts.md`](evaluation-for-hosts.md): scoring and metric explanation.
- [`docs/solution-file-contract.md`](solution-file-contract.md): public-safe solution-file schema.
- [`docs/privacy-and-holdout-custody.md`](privacy-and-holdout-custody.md): public/private artifact boundary.
- [`docs/host-reproducibility-matrix.md`](host-reproducibility-matrix.md): reproducibility matrix.
- [`docs/host-baseline-summary.md`](host-baseline-summary.md): compact baseline summary.
- [`docs/host-architecture.md`](host-architecture.md): Mermaid architecture flowchart.
- [`docs/host-packet-versioning.md`](host-packet-versioning.md): host packet versioning note.
- [`docs/host-private-leakage-response.md`](host-private-leakage-response.md): runbook for private leakage response.
- [`docs/host-review-walkthrough-transcript.md`](host-review-walkthrough-transcript.md): walkthrough transcript for host reviewers.
- [`platform/kaggle/README.md`](../platform/kaggle/README.md): Kaggle integration README.
- [`platform/kaggle/rules-template.md`](../platform/kaggle/rules-template.md): draft rules template for host discussion.
- [`platform/kaggle/competition-page-draft.md`](../platform/kaggle/competition-page-draft.md): competition page overview and timelines.
- [`platform/kaggle/faq.md`](../platform/kaggle/faq.md): FAQ answering host-facing questions.
- [`platform/kaggle/toy_solution_file.csv`](../platform/kaggle/toy_solution_file.csv): example host-side private solution file.

## Contributor And Reviewer

- [`CONTRIBUTING.md`](../CONTRIBUTING.md): contribution rules and privacy
  boundaries.
- [`SECURITY.md`](../SECURITY.md): safe handling guidance.
- [`CHANGELOG.md`](../CHANGELOG.md): release-time change log.
- [`ROADMAP.md`](../ROADMAP.md): milestone view, version labels, and SDLC
  review rhythm.
