# Kaggle-Like Host Review Package

Status: host-review packaging candidate. This page is an entrypoint for a
Kaggle or Kaggle-like benchmark host/reviewer discussion. It does not claim
platform acceptance, hosted leaderboard operation, external validation, or
third-party submissions.

## Review Goal

AuthZBench-SaaS evaluates whether AI agents can prove SaaS authorization
failures with backend-replayable evidence while avoiding false reports on
secure controls. The host-review package answers seven practical questions:

1. What is the benchmark?
2. What would a participant submit?
3. What does the scorer verify?
4. What would a leaderboard row show?
5. Which artifacts are public, private-summary-only, or host-controlled?
6. What validation has passed?
7. What is explicitly not claimed?

## Current Candidate State

- Public target apps: 6 synthetic SaaS applications.
- Public tasks: 60 total, with 24 vulnerable tasks and 36 secure controls.
- Secure controls: 21 denial controls and 15 authorized-allow controls.
- Maintainer-private holdout summaries: 48 tasks summarized publicly, raw
  private holdouts excluded from public Git.
- Public + private task scale: 108 tasks.
- Final host-review candidate commit: use the final PR/merge commit and its
  passing GitHub Actions run before sending a package to a host.

### Validation Levels

| Validation level | Command / source | Requires Docker? | Purpose |
| --- | --- | --- | --- |
| Public no-Docker check | `python3 scripts/validate_public.py --include-scripted-baseline` | No | Fast reviewer validation |
| Full CI host-packet check | `python3 scripts/validate_public.py --include-scripted-baseline --include-container-smoke` | Yes | Containerized smoke and final gate |
| Host-presentation check | `python3 scripts/validate_host_presentation.py` | No | Validates all host-facing artifacts and links |
| Host-presentation with Docker | `python3 scripts/validate_host_presentation.py --include-container-smoke` | Yes | Aggregate validation including Docker |

## What Is Ready For Host Review

- Deterministic public validation and privacy scans.
- Public task manifests and synthetic local target apps.
- Replay-based scoring for authorization evidence.
- Public/private split design and public-safe private-holdout summaries.
- Leaderboard submission schema and validator.
- Baseline registry, task-quality gate, and generated review artifacts.
- Claim-boundary CI checks that prevent stronger public wording from drifting
  into docs.
- Repo-side local Harbor adapter path and runbook, without any platform
  acceptance claim.

## Proposed Host Model

This package proposes Model A (dataset/review package) and Model B (maintainer/host-operated private evaluation pilot) as the first steps.
- **Model A**: This review package is ready now for methodology and reproducibility checks.
- **Model B**: Replay-based scoring pilot uses gitignored private holdout packs to preserve task custody.
- **Model C**: Native CSV-only platform scoring is deferred for this package. CSV functions as a submission index mapping to evidence bundles.

## Host Decisions Still Owned By The Host

- **Custody owner**: Who hosts the private holdout evaluation runners.
- **Submitter artifact**: Confirming if submitters provide result bundles or runner images.
- **Leaderboard row tiering**: Rules for display of public-diagnostic, private-candidate, and host-verified rows.
- **Operational policies**: Reruns, appeals, stale scores, and pack rotation triggers.

## Proposed Review Flow

1. Read this page and [`docs/kaggle-hosting-model.md`](kaggle-hosting-model.md).
2. Read [`docs/evaluation-for-hosts.md`](evaluation-for-hosts.md) for the
   scoring story.
3. Read [`docs/kaggle-presentation-todo.md`](kaggle-presentation-todo.md) for
   the host-presentation checklist.
4. Inspect [`platform/kaggle/README.md`](../platform/kaggle/README.md) and
   [`platform/kaggle/sample_submission.csv`](../platform/kaggle/sample_submission.csv).
5. Inspect [`docs/solution-file-contract.md`](solution-file-contract.md) for
   private solution-file custody rules.
6. Run the public validation command from a fresh clone.
7. Check the final candidate commit's GitHub Actions result.

## Public, Private-Summary, And Host-Controlled Artifacts

| Area | Public in repo | Private-summary only | Host-controlled in a launch |
| --- | --- | --- | --- |
| Public tasks | `tasks/*/*.json` | Not applicable | Public task pack mirrors |
| Private holdouts | Count/fingerprint summaries only | `artifact/private-holdout-*-public-summary.json` | Raw private manifests and solution files |
| Scoring | `authzbench/score.py`, validators, schemas | Redacted aggregate private evidence | Private scorer inputs and raw private outputs |
| Submissions | Schema-valid examples | Redacted private leaderboard rows | Submitted bundles, runner images, accepted rows |
| Validation | CI and public validation scripts | Maintainer-only release evidence summaries | Platform smoke, host audit logs |

## Non-Claims

Do not describe this package as accepted by any platform, as externally
validated, as a hosted leaderboard, as SaaS-provider validated, or as a
production vulnerability discovery benchmark. Use the language in
[`docs/current-claim-boundary.md`](current-claim-boundary.md) when writing a
public summary.

## Host Packet Contents

The host-review package contains the following primary files for host evaluation:

| Reviewer question | File |
| --- | --- |
| One-page summary | [`docs/host-facing-one-page-summary.md`](host-facing-one-page-summary.md) |
| Host model decision | [`docs/kaggle-hosting-model.md`](kaggle-hosting-model.md) |
| Evaluation metric | [`docs/evaluation-for-hosts.md`](evaluation-for-hosts.md) |
| Submission format | [`platform/kaggle/README.md`](../platform/kaggle/README.md), [`platform/kaggle/sample_submission.csv`](../platform/kaggle/sample_submission.csv), [`platform/kaggle/sample_submission.json`](../platform/kaggle/sample_submission.json) |
| Rules draft | [`platform/kaggle/rules-template.md`](../platform/kaggle/rules-template.md) |
| Competition page draft | [`platform/kaggle/competition-page-draft.md`](../platform/kaggle/competition-page-draft.md) |
| Public/private custody | [`docs/privacy-and-holdout-custody.md`](privacy-and-holdout-custody.md) |
| Solution-file contract | [`docs/solution-file-contract.md`](solution-file-contract.md), [`platform/kaggle/toy_solution_file.csv`](../platform/kaggle/toy_solution_file.csv) |
| Reproducibility | [`docs/host-reproducibility-matrix.md`](host-reproducibility-matrix.md) |
| Generated bundle | [`scripts/build_host_review_bundle.py`](../scripts/build_host_review_bundle.py) |

## Related Files

- [`README.md`](../README.md): project overview and claim boundary.
- [`docs/benchmark-card.md`](benchmark-card.md): scope and limitations.
- [`docs/leaderboard-schema.md`](leaderboard-schema.md): row schema and eligibility tiers.
- [`docs/v1-community-submission-governance.md`](v1-community-submission-governance.md): future submission governance.
- [`docs/validation-commands.md`](validation-commands.md): public and maintainer validation commands.
- [`docs/privacy-and-holdout-custody.md`](privacy-and-holdout-custody.md): holdout custody and redaction rules.
- [`docs/kaggle-presentation-todo.md`](kaggle-presentation-todo.md): presentation checklist status.
