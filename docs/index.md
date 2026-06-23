# Documentation Index

Welcome to the AuthZBench-SaaS documentation. This index maps all public-safe documentation, guidelines, and reference reports by role.

---

## 🔍 I am a Host Reviewer / Evaluator
If you are evaluating AuthZBench-SaaS for a Kaggle or Kaggle-like evaluation pilot, start with these host-facing resources:
* **[Reviewer Roadmap (ROADMAP.md)](../ROADMAP.md)**: The authoritative forward-looking roadmap. See the **Reviewer Roadmap At A Glance** section for v1-readiness gaps (owner/verification/status), v2 external-validation prep tracks (dependencies + entry criteria), and repo-presentation polish.
* **[Host Review Package](host/host-review-package.md)**: The central entrypoint for the host packet, questions, and scopes.
* **[Host Status & Reproducibility Matrix](host/host-status-and-reproducibility.md)**: Live status, reproducibility matrix, and versioning.
* **[Hosting Model Options](host/hosting-model.md)**: Decisions on data custody, metric details, solution-file contracts, and display policies.
* **[Host Operations Runbook](host/host-operations-runbook.md)**: Leakage response protocols, privacy boundaries, and rotation guidelines.
* **[Host Walkthrough Transcript](host/host-review-walkthrough.md)**: Walkthrough script of validator execution.

*Note: Kaggle integration templates (such as rules, FAQ, and drafts) live in [platform/kaggle/](../platform/kaggle/README.md).*

---

## 💻 I am a Developer / Task Author
If you are running evaluations, reviewing code, or adding new tasks to the benchmark:
* **[Benchmark Specification](benchmark-spec.md)**: Benchmark design, evaluation split, and claim boundaries.
* **[Task Quality Rubric](task-quality-rubric.md)**: Guidelines for writing new vulnerable and secure control tasks.
* **[Scoring & Submissions Guide](scoring-and-submissions.md)**: Replay-based scoring mechanics, submission schema, and anti-gaming policy.
* **[Harbor Integration Runbook](harbor-integration-runbook.md)**: Scaffolding, parity validator, and CLI commands for Harbor adapters.
* **[v1 Readiness Checklist](v1-readiness-checklist.md)**: The release checklist and preflight gates for v1.
* **[Validation Commands](validation-commands.md)**: Guide to running public, maintainer, and privacy checks.
* **[Task Taxonomy](task-taxonomy.md)**: Taxonomy of vulnerability families and control distributions.
* **[Holdout Rotation Protocol](holdout-rotation-protocol.md)**: Rotating private holdout packs.
* **[Private Holdout Lifecycle](private-holdout-lifecycle.md)**: Lifecycle policies for candidate and active private packs.

---

## 📑 Reference Materials & Archive
* **[Claims and Evidence](claims-and-evidence.md)**: Canonical claim mapping table and v2 validation tracks.
* **[Artifact Index](artifact-index.md)**: Allowed claims and purposes for each public-safe artifact.
* **[v0.0 Technical Report](authzbench-saas-v0.0-technical-report.md)** & **[v1-Prep Technical Report](authzbench-saas-v1-prep-technical-report.md)**: Technical reports/papers.
* **[Launch Report](launch-report.md)**: Historical benchmark launch report.
* **[Submission Governance Spec](v1-community-submission-governance.md)**: Specifications for future community submissions.
