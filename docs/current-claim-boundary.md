# Current Claim Boundary

This document is the canonical, single-table claim ledger for
AuthZBench-SaaS. It exists so reviewers do not have to reconcile the README,
benchmark card, evidence matrix, Harbor docs, and release artifacts
manually.

It is intentionally short, declarative, and tied directly to the evidence
artifacts the repository ships. When something changes, this table is
updated first, and the linked docs are updated to match.

## Top-level interpretation note

`v1_ready: true` in
[`artifact/expected-output/v1-readiness-public-view.json`](artifact/expected-output/v1-readiness-public-view.json)
is scoped to the **internal / public-view** readiness gates only. It is the
output of the ten internal gates listed in
[`docs/v1-readiness-checklist.md`](v1-readiness-checklist.md). It does
**not** assert external review, SaaS-provider validation, hosted public
leaderboard readiness, or platform acceptance. v2 / external gates are
tracked in
[`docs/v2-external-validation-roadmap.md`](v2-external-validation-roadmap.md).

The `local_or_containerized_submission_smoke` gate covers the local Docker
submission smoke only and explicitly sets
`hosted_leaderboard_operation_claimed: false`. The previous gate name
`hosted_or_containerized_submission_execution` was renamed to remove the
"hosted" wording from the gate itself, because the gate never proved hosted
operation.

The `has_current_public_tool_agent_baseline` field in the baseline registry
has been replaced by two more honest fields:

- `has_current_public_scripted_sanity_baseline: true` — a deterministic
  scripted sanity row is present and re-run on the current 60-task public
  split. This is a harness check, **not** a model or tool-agent capability
  result.
- `has_current_public_model_or_tool_agent_baseline: true` — at least one
  fresh 60-task repeated run exists for a model or live-HTTP tool-agent
  baseline, with target-request correlation when live HTTP is used.

## Canonical claim table

| Claim | Status | Evidence | Forbidden stronger wording |
| --- | --- | --- | --- |
| `v1.0-internal` complete | Supported | `docs/releases/v1.0-internal.md`, the ten internal gates listed in `docs/v1-readiness-checklist.md`, and `artifact/expected-output/v1-readiness-public-view.json` | "community benchmark", "externally validated benchmark", "leaderboard-grade benchmark" |
| 60 public tasks | Supported | `tasks/` (6 apps × 10 tasks), `docs/task-quality-matrix.md`, the v1-prep public split | "leaderboard-grade public split" |
| 48 private holdout tasks | Supported by fingerprint / count | `tasks_private/holdout/rotation-metadata.json`, `artifact/private-holdout-active-public-summary.json`, the `validated_private_holdout_task_count=48` evidence line in the public-view fixture | "publicly reproducible private holdouts", "open private holdout task list" |
| Local Harbor adapter path | Supported | `authzbench_harbor/`, `docs/harbor-integration-runbook.md`, `artifact/harbor-adapter-smoke.json`, the parity methodology versioning evidence | "Harbor accepted", "Harbor endorsed", "Harbor leaderboard-ready" |
| Local / containerized submission smoke | Supported | `artifact/submission-runner-smoke.json`, `artifact/hosted-submission-execution-runbook.json`, the `local_or_containerized_submission_smoke` gate | "hosted leaderboard", "hosted submission operation" |
| Deterministic backend-replay scorer | Supported | `authzbench/scorer/`, `docs/score-policy.md`, `docs/score-stability-policy.md` | "human-judged scoring", "model-graded scoring" |
| Public / private split with holdout governance | Supported | `docs/holdout-and-contamination.md`, `docs/holdout-rotation-protocol.md`, `docs/v1-community-submission-governance.md` | "public leaderboard operation", "open private holdout reuse" |
| Current scripted sanity baseline | Supported | `baselines/baseline-registry.json` `scripted-sanity-public-60` entry, `baselines/scripted-baseline-public-60-summary.json` | "current model baseline", "current tool-agent baseline" |
| Fresh 60-task model / tool-agent baseline | Supported for the families listed in `baselines/baseline-registry.json` with `release_suitability: current_public_split` | repeated `kiro-*current-public-60` summary JSONs in `baselines/` | "all major model families", "all current frontier models" |
| Synthetic targets only | Supported | `apps/`, the absence of any real-SaaS integration in tracked files | "production SaaS coverage", "real customer SaaS authorization coverage" |
| Independent external review | Not done | `docs/reviews/external-review-packet.md` (packet only, no reviewer dispositions) | "external review complete", "industry-standard benchmark" |
| SaaS-provider scenario validation | Not done | `docs/v2-external-validation-roadmap.md` (v2 lane) | "SaaS-validated", "real-world validated", "AppSec-reviewed" |
| Hosted public leaderboard | Not done | `docs/v2-external-validation-roadmap.md`, `artifact/hosted-submission-execution-runbook.json` (runbook only) | "hosted leaderboard-ready", "hosted leaderboard operation" |
| Harbor / Kaggle / other platform acceptance | Not done | `artifact/harbor-adapter-readiness-blockers.json`, the `harbor_execution_verified=False` evidence line in the public-view fixture | "Harbor accepted", "Harbor endorsed", "Kaggle accepted" |
| Third-party submissions | Not done | `docs/v1-community-submission-governance.md` (governance only) | "open for third-party submissions", "community submission open" |
| v1 release-ready | Not done | the v1.0-internal cut exists, but the public-view and release-candidate evidence are not externally validated | "v1 release-ready", "v1.0 released" |

## How to use this table

- For README text, release notes, benchmark card, LinkedIn posts, or
  external-review notes, copy the **Status** column verbatim. Do not
  paraphrase "Supported" into "we have completed", and do not paraphrase
  "Not done" into "in progress" or "coming soon".
- For "Forbidden stronger wording" enforcement, run
  `python3 scripts/check_claim_boundary.py`. See
  [`scripts/check_claim_boundary.py`](../scripts/check_claim_boundary.py)
  and [`tests/test_claim_boundary_check.py`](../tests/test_claim_boundary_check.py).
- When a row's Status changes, update this table first, then the linked
  docs, then the validator evidence lines. The validator's
  `interpretation_note` evidence lines in the public-view fixture are
  generated from the same sources as this table.

## Linked sources

- [`README.md`](../README.md) — top-level orientation
- [`docs/evidence-and-claims.md`](evidence-and-claims.md) — detailed
  evidence matrix and the historical per-evidence ledger
- [`docs/benchmark-card.md`](benchmark-card.md) — benchmark scope and
  intended use
- [`docs/v2-external-validation-roadmap.md`](v2-external-validation-roadmap.md) —
  v2 / external validation lanes
- [`docs/v1-readiness-checklist.md`](v1-readiness-checklist.md) — the ten
  internal gates and their pass / fail state
- [`docs/releases/v1.0-internal.md`](releases/v1.0-internal.md) — the
  `v1.0-internal` release note
- [`docs/harbor-integration-runbook.md`](harbor-integration-runbook.md) —
  Harbor adapter runbook
