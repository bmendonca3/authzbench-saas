# Documentation Index

Welcome to the AuthZBench-SaaS documentation. This index maps all public-safe documentation, guidelines, and reference reports by role.

---

## 🔍 I am a Host Reviewer / Evaluator
If you are evaluating AuthZBench-SaaS for a Kaggle or Kaggle-like evaluation pilot, start with these host-facing resources:
* **[Host Review Package](host-review-package.md)**: The central entrypoint for the host packet, questions, and scopes.
* **[Host Reproducibility Matrix](host-reproducibility-matrix.md)**: Verification statuses, commands, and CI reference logs.
* **[Kaggle Hosting Model Options](kaggle-hosting-model.md)**: Proposals for data custody, display policy, and evaluation metrics.
* **[One-Page Benchmark Summary](host-facing-one-page-summary.md)**: A high-level overview of the benchmark's core concepts.
* **[Host Versioning Note](host-packet-versioning.md)**: Reference hashes, citation formats, and tag policies.
* **[Host Walkthrough Transcript](host-review-walkthrough-transcript.md)**: Walkthrough script of exact command execution and verification.
* **[Host Operations Runbook](host-private-leakage-response.md)**: Operational protocols for rotating holdouts and leakage response.
* **[Evaluation for Hosts](evaluation-for-hosts.md)**: Details on metrics, rewards, and scoring tiers.
* **[Solution-File Contract](solution-file-contract.md)**: Schema contract for the host-side private solution CSV.
* **[Privacy and Holdout Custody](privacy-and-holdout-custody.md)**: Defining the boundaries of public-safe and host-only files.
* **[Host Presentation Checklist](kaggle-presentation-todo.md)**: Status of prep tasks and open host decisions.

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
