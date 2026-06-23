# Kaggle-Like Host FAQ

## Is this a live Kaggle competition today?
No. This repository packages a host-review candidate for a proposed benchmark discussion. It is not an active or live competition, and there is no hosted leaderboard running at this time.

## Is this Kaggle accepted or endorsed?
No. The project does not claim platform acceptance, platform endorsement, hosted leaderboard operation, or external validation. The term "Kaggle-like" describes the format and structure of the proposed review packet, which is designed to match platform-hosting standards.

## Why not just submit labels in a CSV?
Because AuthZBench-SaaS rewards backend-replayable authorization proof and penalizes false reports on secure controls. A label-only CSV cannot show whether the agent actually touched the target backend, generated replayable evidence, respected scope, or avoided over-reporting secure controls.

## What exactly does the CSV prove?
In this package, the CSV functions as a submission index or manifest. It maps task IDs to the finding files inside the participant's evidence bundle. It does not serve as standalone label-scoring evidence.

## What does the evidence bundle contain?
The evidence bundle contains per-task `submission.json` files. For vulnerable tasks, this includes exploit findings, targeted HTTP request logs, and resource boundaries. For secure-control tasks, it contains a declaration of no findings.

## What is leaderboard eligible?
Only submissions evaluated against the private split using host-controlled or maintainer-operated private runs are eligible for the private leaderboard-candidate rows, subject to evidence replay and verification.

## What is diagnostic only?
The public split (60 tasks) is diagnostic only. It is intended for local validation and debugging. Public split rows are never eligible for the private leaderboard-candidate rows.

## How are private holdouts protected?
Private holdouts are stored in a separate directory (`tasks_private/`) that is excluded from the public Git history and ignored. Only aggregate fingerprints and public-safe summaries are checked in. Scorer runs read private tasks in a restricted environment.

## What happens if private leakage occurs?
If private task manifests are leaked, the host will rotate the active private pack to a new shadow pack version, regenerate manifest fingerprints, and invalidate affected scores following the protocol in `docs/host/host-operations-runbook.md`.

## What must a host decide before launch?
The host must decide:
- **Custody owner**: Who hosts the private holdout evaluation runners.
- **Submitter artifact**: Confirming if submitters provide result bundles or runner images.
- **Leaderboard-candidate row tiering**: Rules for display of public-diagnostic, private-candidate, and host-verified rows.
- **Operational policies**: Reruns, appeals, stale scores, and pack rotation triggers.

## Can this become native Kaggle scoring later?
Yes. If the host adopts a container-based execution model (Model B), the target apps and scorer can run inside a Kaggle sandbox environment to score participant agents natively on the platform.
