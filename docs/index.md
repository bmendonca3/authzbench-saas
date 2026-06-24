# Documentation Index

Welcome to the AuthZBench-SaaS documentation. This index maps all public-safe documentation, guidelines, and reference reports by role.

---

## 🔍 I am a Host Reviewer / Evaluator
If you are doing host reviewer or evaluator preparation, start with these host-facing resources. This is host reviewer or evaluator preparation, not platform acceptance, not hosted leaderboard operation, and not third-party submissions; these tracks are v2-deferred.
* **[Reviewer Roadmap (ROADMAP.md)](../ROADMAP.md)**: The authoritative forward-looking roadmap. See the **Reviewer Roadmap At A Glance** section for roadmap gaps (owner/verification/status), v2 external-validation prep tracks (dependencies + entry criteria), and repo-presentation polish.
* **[Reviewer Walkthrough](reviewer-walkthrough.md)**: Step-by-step reviewer guide covering public-view readiness fixture match (`--allow-incomplete`), validation levels, and claim boundaries.
* **[v1.0-internal Release Note](releases/v1.0-internal.md)**: v1.0-internal public-view readiness fixture state, task scale, and what is not claimed.
* **[Claims and Evidence](claims-and-evidence.md)**: Canonical claim ledger, evidence matrix, and v2 deferred validation tracks.
* **[Validation Commands](validation-commands.md)**: Public, host, Docker, and maintainer-only validation commands with failure guidance.
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
* **[Baseline Credibility](baseline-credibility.md)**: Baseline registry labels, current scripted sanity interpretation, and stale/historical baseline guidance.
* **[Baseline Rerun Readiness Runbook](baseline-rerun-readiness-runbook.md)**: Exact commands, prerequisites, and post-run steps for rerunning model and tool-agent baselines at the current 63-task public split.
* **[Harbor Integration Runbook](harbor-integration-runbook.md)**: Scaffolding, parity validator, and CLI commands for Harbor adapters.
* **[v1 Readiness Checklist](v1-readiness-checklist.md)**: The release checklist and public-view readiness fixture gates for v1.0-internal.
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
* **[Submission Governance Spec](v1-community-submission-governance.md)**: Governance for future hosted/community submission tracks with local row eligibility.
