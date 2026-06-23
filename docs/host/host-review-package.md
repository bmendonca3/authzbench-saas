# Kaggle-Like Host Review Package

Status: host-review packaging candidate. This page is an entrypoint for a Kaggle or Kaggle-like benchmark host/reviewer discussion. It does not claim platform acceptance, hosted leaderboard operation, external validation, or third-party submissions.

## Review Goal

AuthZBench-SaaS evaluates whether AI agents can prove SaaS authorization failures with backend-replayable evidence while avoiding false reports on secure controls. The host-review package answers seven practical questions:

1. What is the benchmark?
2. What would a participant submit?
3. What does the scorer verify?
4. What would a leaderboard-candidate row show?
5. Which artifacts are public, private-summary-only, or host-controlled?
6. What validation has passed?
7. What is explicitly not claimed?

## Current Candidate State

* **Public target apps**: 6 synthetic SaaS applications.
* **Public tasks**: 63 total, with 27 vulnerable tasks and 36 secure controls.
* **Secure controls**: 21 denial controls and 15 authorized-allow controls.
* **Maintainer-private holdout summaries**: 48 tasks summarized publicly, raw private holdouts excluded from public Git.
* **Public + private task scale**: 111 tasks.
* **Final host-review candidate commit**: use the final PR/merge commit and its passing GitHub Actions run before sending a package to a host. The exact reviewed commit and CI run are recorded in [Host Status & Reproducibility Matrix](host-status-and-reproducibility.md).

### Validation Levels

| Validation level | Command / source | Requires Docker? | Purpose |
| --- | --- | --- | --- |
| Public no-Docker check | `python3 scripts/validate_public.py --include-scripted-baseline` | No | Fast reviewer validation |
| Full CI host-packet check | `python3 scripts/validate_public.py --include-scripted-baseline --include-container-smoke` | Yes | Containerized smoke and final gate |
| Host-presentation check | `python3 scripts/validate_host_presentation.py` | No | Validates all host-facing artifacts and links |
| Host-presentation with Docker | `python3 scripts/validate_host_presentation.py --include-container-smoke` | Yes | Aggregate validation including Docker |

## What Is Ready For Host Review

* Deterministic public validation and privacy scans.
* Public task manifests and synthetic local target apps.
* Replay-based scoring for authorization evidence.
* Public/private split design and public-safe private-holdout summaries.
* Leaderboard submission schema and validator.
* Baseline registry, task-quality gate, and generated review artifacts.
* Claim-boundary CI checks that prevent stronger public wording from drifting into docs.
* Repo-side local Harbor adapter path and runbook, without any platform acceptance claim.

## Proposed Host Model

This package proposes Model A (dataset/review package) and Model B (maintainer/host-operated private evaluation pilot) as the first steps.
* **Model A**: This review package is ready now for methodology and reproducibility checks.
* **Model B**: Replay-based scoring pilot uses gitignored private holdout packs to preserve task custody.
* **Model C**: Native CSV-only platform scoring is deferred for this package. CSV functions as a submission index mapping to evidence bundles.

## Host Decisions Still Owned By The Host

* **Custody owner**: Who hosts the private holdout evaluation runners.
* **Submitter artifact**: Confirming if submitters provide result bundles or runner images.
* **Leaderboard-candidate row tiering**: Rules for display of public-diagnostic, private-candidate, and host-verified rows.
* **Operational policies**: Reruns, appeals, stale scores, and pack rotation triggers.

## Proposed Review Flow

1. Read this page and [Hosting Model Options](hosting-model.md).
2. Read [Host Status & Reproducibility Matrix](host-status-and-reproducibility.md) for the live verification statuses.
3. Read the [Host Operations Runbook](host-operations-runbook.md) for data custody protocols.
4. Inspect [Kaggle Integration README](../../platform/kaggle/README.md) and [Sample Submission CSV](../../platform/kaggle/sample_submission.csv).
5. Inspect [Hosting Model Options](hosting-model.md) for private solution-file custody rules and metrics.
6. Run the public validation command from a fresh clone.
7. Check the final candidate commit's GitHub Actions result.

## Public, Private-Summary, And Host-Controlled Artifacts

| Area | Public in repo | Private-summary only | Host-controlled in a launch |
| --- | --- | --- | --- |
| Public tasks | `tasks/*/*.json` | Not applicable | Public task pack mirrors |
| Private holdouts | Count/fingerprint summaries only | `artifact/private-holdout-*-public-summary.json` | Raw private manifests and solution files |
| Scoring | `authzbench/score.py`, validators, schemas | Redacted aggregate private evidence | Private scorer inputs and raw private outputs |
| Submissions | Schema-valid examples | Redacted private leaderboard-candidate rows | Submitted bundles, runner images, accepted rows |
| Validation | CI and public validation scripts | Maintainer-only release evidence summaries | Platform smoke, host audit logs |

## Non-Claims

Do not describe this package as accepted by any platform, as externally validated, as a hosted leaderboard, as SaaS-provider validated, or as a production vulnerability discovery benchmark. Use the language in [Claims and Evidence](../claims-and-evidence.md) when writing a public summary.

## Host Packet Contents

The host-review package contains the following primary files for host evaluation:

| Reviewer question | File |
| --- | --- |
| One-page summary & Host model decision | [Hosting Model Options](hosting-model.md) |
| Evaluation metric & Solution contract | [Hosting Model Options](hosting-model.md) |
| Submission format | [Kaggle Integration README](../../platform/kaggle/README.md), [Sample Submission CSV](../../platform/kaggle/sample_submission.csv), [Sample Submission JSON](../../platform/kaggle/sample_submission.json) |
| Rules draft | [Rules Template](../../platform/kaggle/rules-template.md) |
| Competition page draft | [Competition Page Draft](../../platform/kaggle/competition-page-draft.md) |
| Public/private custody & Operations runbook | [Host Operations Runbook](host-operations-runbook.md) |
| Reproducibility & Verification Status | [Host Status & Reproducibility Matrix](host-status-and-reproducibility.md) |
| Generated bundle | [Build Host Review Bundle Script](../../scripts/build_host_review_bundle.py) |

## Related Files

* [README.md](../../README.md): project overview and claim boundary.
* [Benchmark Spec](../benchmark-spec.md): scope, thesis, methodology, and limitations.
* [Scoring and Submissions](../scoring-and-submissions.md): row schema, eligibility tiers, and scoring policy.
* [Submission Governance Specification](../v1-community-submission-governance.md): future submission governance.
* [Validation Commands](../validation-commands.md): public and maintainer validation commands.
