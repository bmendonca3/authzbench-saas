# Documentation Index

Welcome to the AuthZBench-SaaS documentation. This index maps all public-safe documentation, guidelines, and reference reports by role.

---

## 🔍 I am a Host Reviewer / Evaluator
If you are evaluating AuthZBench-SaaS for a Kaggle or Kaggle-like evaluation pilot, start with these host-facing resources:
* **[Host Review Package](host/host-review-package.md)**: The central entrypoint for the host packet, questions, and scopes.
* **[Host Status & Reproducibility Matrix](host/host-status-and-reproducibility.md)**: Live status, reproducibility matrix, and versioning.
* **[Hosting Model Options](host/hosting-model.md)**: Decisions on data custody, metric details, solution-file contracts, and display policies.
* **[Host Operations Runbook](host/host-operations-runbook.md)**: Leakage response protocols, privacy boundaries, and rotation guidelines.
* **[Host Walkthrough Transcript](host/host-review-walkthrough.md)**: Walkthrough script of validator execution.

*Note: Kaggle integration templates (such as rules, FAQ, and drafts) live in [platform/kaggle/](../platform/kaggle/README.md).*

---

## 💻 I am a Developer / Task Author
If you are running evaluations, reviewing code, or adding new tasks to the benchmark:
* **[Methodology Guide](methodology.md)**: Benchmark design, evaluation split, and claim boundaries.
* **[Task Quality Rubric](task-quality-rubric.md)**: Guidelines for writing new vulnerable and secure control tasks.
* **[Scorer Policy](score-policy.md)** & **[Scoring Examples](scoring-examples.md)**: Replay-based scoring mechanics and examples.
* **[Harbor Integration Runbook](harbor-integration-runbook.md)**: Scaffolding, parity validator, and CLI commands for Harbor adapters.
* **[v1 Readiness Checklist](v1-readiness-checklist.md)**: The release checklist and preflight gates for v1.
* **[Validation Commands](validation-commands.md)**: Guide to running public, maintainer, and privacy checks.
* **[Task Taxonomy](task-taxonomy.md)**: Taxonomy of vulnerability families and control distributions.
* **[Holdout and Contamination](holdout-and-contamination.md)**: Holdout isolation and contamination controls.
* **[Holdout Rotation Protocol](holdout-rotation-protocol.md)**: Rotating private holdout packs.
* **[Private Holdout Lifecycle](private-holdout-lifecycle.md)**: Lifecycle policies for candidate and active private packs.

---

## 📑 Reference Materials & Archive
* **[Current Claim Boundary](current-claim-boundary.md)**: Canonical claim mapping table.
* **[Leaderboard Schema](leaderboard-schema.md)**: Row layout and eligible tiers for public submissions.
* **[Anti-Gaming Policy](leaderboard-anti-gaming-policy.md)**: Anti-gaming metrics and split validation.
* **[Artifact Index](artifact-index.md)**: Allowed claims and purposes for each public-safe artifact.
* **[v0.0 Technical Report](authzbench-saas-v0.0-technical-report.md)** & **[v1-Prep Technical Report](authzbench-saas-v1-prep-technical-report.md)**: Technical reports/papers.
* **[Launch Report](launch-report.md)**: Historical benchmark launch report.
* **[v2 External Validation Roadmap](v2-external-validation-roadmap.md)**: Outline of validation tracks deferred to v2.
* **[Submission Governance Spec](v1-community-submission-governance.md)**: Specifications for future community submissions.
