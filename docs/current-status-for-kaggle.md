# Current Status for Kaggle

Status: single-page status summary for Kaggle host reviewers. This document
says what is done, what is pending from Kaggle, and what review is being
requested. It does not claim platform acceptance, hosted leaderboard operation,
external validation, or third-party submissions.

**Last updated**: 2026-06-16
**Current commit**: `eeea4be` on branch `kaggle-host-review-package`
**CI status**: All validation gates passing

---

## What Is Done (Repo-Side)

### Benchmark Core
- [x] 60 public tasks across 6 synthetic SaaS applications (24 vulnerable, 36 secure controls)
- [x] 48 private holdout tasks (summarized publicly, raw manifests gitignored)
- [x] Replay-based scorer with adversarial submission hardening
- [x] Public validation suite: `python3 scripts/validate_public.py --include-scripted-baseline`
- [x] Host-presentation validator: `python3 scripts/validate_host_presentation.py`
- [x] 518+ unit tests passing locally

### Harbor Integration
- [x] Harbor-compatible dataset skeleton builder and validator
- [x] Local Harbor execution smoke verified (`artifact/harbor-adapter-smoke.json`)
- [x] Per-task reward parity verified: **6/6 tasks, 100% match rate** (`artifact/harbor-parity-experiment.json`)
- [x] Harbor adapter metadata documented (`artifact/harbor-adapter-metadata.json`)

### Host-Review Package
- [x] Host-review package document (`docs/host-review-package.md`)
- [x] Hosting model decision memo (`docs/kaggle-hosting-model.md`)
- [x] Host-facing one-page summary (`docs/host-facing-one-page-summary.md`)
- [x] Reproducibility matrix with CI verification (`docs/host-reproducibility-matrix.md`)
- [x] Claim-boundary CI checks preventing wording drift
- [x] Sample submission, dry-run bundle, toy solution validators
- [x] Host review bundle builder and validator

### Review Readiness
- [x] External review packet (`docs/reviews/external-review-packet.md`)
- [x] AppSec review packet (`docs/reviews/appsec-review-packet.md`)
- [x] Agent/tooling review packet (`docs/reviews/agent-tooling-review-packet.md`)
- [x] Benchmark methodology review packet (`docs/reviews/benchmark-methodology-review-packet.md`)
- [x] SaaS-provider review packet (`docs/reviews/saas-provider-review-packet.md`)
- [x] Review intake form and response templates

---

## What Is Pending From Kaggle

| Item | What We Need | Who Decides |
| --- | --- | --- |
| Docker execution spec | Confirm expected container shape, metadata paths, artifact format, scoring interface | Kaggle |
| Platform acceptance | Accept or decline to host the benchmark | Kaggle |
| Hosted leaderboard | Set up leaderboard infrastructure if accepted | Kaggle |
| Private holdout execution environment | Provide or approve a host-controlled runner for private evaluation | Kaggle / Maintainer |

---

## What Is Pending From External Reviewers

| Review Lane | Reviewer Profile | Packet Ready? | Review Started? |
| --- | --- | --- | --- |
| Application security | AppSec practitioner | Yes | No |
| Benchmark/evals methodology | Evals researcher | Yes | No |
| AI-agent/tooling | Agent/tooling engineer | Yes | No |
| SaaS-provider validation | Product-security team | Yes | No |

---

## What We Are Asking For

1. **Methodology review**: Is the benchmark design (replay-based scoring, public/private split, controls mix) sound for a Kaggle-like pilot?
2. **Docker spec confirmation**: What container shape and artifact paths does Kaggle expect?
3. **Hosting model decision**: We propose Model A (review package) + Model B (maintainer-operated private evaluation). See [`docs/kaggle-hosting-model.md`](kaggle-hosting-model.md).
4. **Next steps timeline**: When can we schedule independent external reviews?

---

## Quick Start for Reviewers

```bash
# Clone and validate
git clone https://github.com/bmendonca3/authzbench-saas.git
cd authzbench-saas
git checkout kaggle-host-review-package

# Run public validation (no Docker required)
python3 scripts/validate_public.py --include-scripted-baseline

# Run host-presentation validator
python3 scripts/validate_host_presentation.py --allow-dirty

# Run all unit tests
python3 -m unittest discover -s tests
```

---

## Key Entry Points

| Document | Purpose |
| --- | --- |
| [`host-review-package.md`](host-review-package.md) | Full host-review packet |
| [`kaggle-hosting-model.md`](kaggle-hosting-model.md) | Hosting model options |
| [`kaggle-harbor-integration-brief.md`](kaggle-harbor-integration-brief.md) | Harbor integration summary |
| [`host-facing-one-page-summary.md`](host-facing-one-page-summary.md) | One-page benchmark summary |
| [`host-reproducibility-matrix.md`](host-reproducibility-matrix.md) | Validation matrix with CI refs |
| [`current-claim-boundary.md`](current-claim-boundary.md) | What we do and do not claim |

## Explicit Non-Claims

This document does not claim platform acceptance, hosted leaderboard operation,
external validation completion, SaaS-provider validation, Harbor acceptance,
or third-party submissions.
