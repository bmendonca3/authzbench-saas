# Host Status and Reproducibility Matrix

Status: single-page status and reproducibility summary for Kaggle host reviewers. This page tracks reference hashes, versions, and validation statuses to ensure host packet reproducibility. It does not claim platform acceptance, hosted leaderboard operation, external validation, or third-party submissions.

---

## 1. Current Status

* **Last updated**: 2026-06-26
* **Current candidate**: 63-task Kaggle/Harbor host-review package update on branch `main`; use the exact commit and latest green GitHub Actions run for the checkout under review.
* **Local validation**: rerun on 2026-06-26 for this candidate package; rerun after any follow-up change before calling a future package frozen.
* **CI validation**: exact-head CI is required before freezing or sharing a package. Historical references below are retained as prior evidence, not as claims about later commits.

### What Is Done (Repo-Side)

#### Benchmark Core
* [x] 63 public tasks across 6 synthetic SaaS applications (27 vulnerable, 36 secure controls)
* [x] 48 private holdout tasks (summarized publicly, raw manifests gitignored)
* [x] Replay-based scorer with adversarial submission hardening
* [x] Public validation suite: `python3 scripts/validate_public.py --include-scripted-baseline`
* [x] Host-presentation validator: `python3 scripts/validate_host_presentation.py`
* [x] Unit test suite passing locally

#### Harbor Integration
* [x] Harbor-compatible dataset skeleton builder and validator
* [x] Local Harbor execution smoke verified (`artifact/harbor-adapter-smoke.json`)
* [x] Per-task reward parity verified: **6/6 tasks, 100% match rate** (`artifact/harbor-parity-experiment.json`)
* [x] Harbor adapter metadata documented (`artifact/harbor-adapter-metadata.json`)

Public CI may still report `harbor_execution_verified=false` when the Harbor CLI is not installed in the runner. That is an environment-availability flag, separate from the checked-in local Harbor smoke and parity evidence above.

#### Host-Review Package
* [x] Host-review package document ([Host Review Package](host-review-package.md))
* [x] Hosting model decision memo ([Hosting Model Options](hosting-model.md))
* [x] Host-facing one-page summary ([Hosting Model Options](hosting-model.md))
* [x] Reproducibility matrix with CI verification (see below)
* [x] Claim-boundary CI checks preventing wording drift
* [x] Sample submission, dry-run bundle, toy solution validators
* [x] Host review bundle builder and validator

#### Review Readiness
* [x] External review packet (`docs/reviews/external-review-packet.md`)
* [x] AppSec, Agent/Tooling, Benchmark Evals, and SaaS-Provider review packets
* [x] Review intake form and response templates

---

## 2. What Is Pending From Host (Kaggle)

| Item | What We Need | Who Decides |
| --- | --- | --- |
| Docker execution spec | Confirm expected container shape, metadata paths, artifact format, scoring interface | Kaggle |
| Host disposition | Accept, defer, or decline hosting the benchmark | Kaggle |
| Leaderboard infrastructure | Set up hosted scoring and display infrastructure if accepted | Kaggle |
| Private holdout execution environment | Provide or approve a host-controlled runner for private evaluation | Kaggle / Maintainer |

---

## 3. What Is Pending From External Reviewers

| Review Lane | Reviewer Profile | Packet Ready? | Review Started? |
| --- | --- | --- | --- |
| Application security | AppSec practitioner | Yes | No |
| Benchmark/evals methodology | Evals researcher | Yes | No |
| AI-agent/tooling | Agent/tooling engineer | Yes | No |
| SaaS-provider validation (Optional v2 track) | Product-security team | Yes | No |

---

## 4. Reproducibility Matrix

| Surface | Command / Evidence | Status / Last Checked UTC | Checked By | Environment (OS/Python) | Re-run Command / Failure Action |
| --- | --- | --- | --- | --- | --- |
| **Public Validation** | `python3 scripts/validate_public.py --include-scripted-baseline` | `2026-06-26 local` | Maintainer | macOS / Python 3.11 | `python3 scripts/validate_public.py --include-scripted-baseline` / Fail on errors |
| **Full CI Validation** | Latest green GitHub Actions run on branch `main` | Required for the exact commit under review | CI Runner | Ubuntu / Python 3.11 | Inspect Actions logs / Fail on CI failures |
| **Container Smoke** | `--include-container-smoke` | Required in CI for the exact commit under review | CI Runner | Ubuntu / Python 3.11 (with Docker) | Check containerized logs / Fail on Docker errors |
| **Host-Presentation** | `python3 scripts/validate_host_presentation.py --skip-public-validation --timeout-seconds 120` | `2026-06-26 local` | Maintainer | macOS / Python 3.11 | `python3 scripts/validate_host_presentation.py` / Fail on link or template mismatch |
| **Review Bundle Check** | `python3 scripts/build_host_review_bundle.py --check` | `2026-06-26 local` | Maintainer | macOS / Python 3.11 | `python3 scripts/build_host_review_bundle.py --check` / Regenerate manifest if out of sync |
| **Public Sample CSV** | `python3 scripts/validate_kaggle_sample_submission.py` | `2026-06-26 local` | Maintainer | macOS / Python 3.11 | `python3 scripts/validate_kaggle_sample_submission.py` / Fix format mismatch |
| **Dry-Run Bundle** | `python3 scripts/validate_kaggle_dry_run_bundle.py` | `2026-06-26 local` | Maintainer | macOS / Python 3.11 | `python3 scripts/validate_kaggle_dry_run_bundle.py` / Check dry-run files |
| **Private Holdout Custody** | active/shadow count and fingerprint summaries | Summarized in `docs/private-holdout-lifecycle.md` and `docs/host/host-operations-runbook.md` | Maintainer | Not applicable | Review custody boundary / Check manifest.json |
| **Host Model** | Model A + Model B (Model C deferred) | Decision recorded in hosting memo | Maintainer | Not applicable | Host accepts or changes proposal |

### CI Verification Reference
* **Latest Verified Commit**: the exact commit under review must match the latest green branch run before freezing or sharing the package.
* **Latest branch run**: https://github.com/bmendonca3/authzbench-saas/actions/workflows/validate.yml?query=branch%3Amain
* **Conclusion required before freezing**: `success` on the exact commit under review.
* **Historical CI-verified candidate**: `bba7007e7bac50ac69d32f650e461869228baa1d` in Actions run `28057052847`.
* **Scope note**: Historical runs support continuity only. A final host-review candidate requires a fresh exact-head validation and CI reference.

---

## 5. Host Packet Versioning

### Reference Versions
* **Repository Commit SHA**: use the exact commit under review from `git rev-parse HEAD` and the matching green Actions run.
* **Historical CI-Verified Candidate SHA**: `bba7007e7bac50ac69d32f650e461869228baa1d`
* **Historical Actions Workflow Run ID**: `28057052847`
* **Host Review Bundle Manifest SHA-256**: [Generated at build time]
* **Active Private Pack Public-Summary Fingerprint SHA-256**: `6b8b51c03492238c881b737029e7802d4127ab2a53655db2b7d5bf25032ba7c8`

### Citation Format
```bibtex
@misc{authzbench2026saas,
  title={AuthZBench-SaaS: Evidence-Based SaaS Authorization Evaluation},
  author={AuthZBench Team},
  year={2026},
  howpublished={\url{https://github.com/bmendonca3/authzbench-saas}},
  note={Host Review Package Candidate Commit to be resolved from the exact reviewed checkout}
}
```

### Update Policy
This host review packet should be frozen only after exact-head public validation, host-presentation validation, privacy checks, and CI pass on the final candidate commit. Any subsequent changes to tasks, scorers, or rules templates trigger a new candidate commit and manifest regeneration.

---

## 6. Quick Start for Reviewers

```bash
# Clone and validate
git clone https://github.com/bmendonca3/authzbench-saas.git
cd authzbench-saas
git checkout main

# Run public validation (no Docker required)
python3 scripts/validate_public.py --include-scripted-baseline

# Run host-presentation validator
python3 scripts/validate_host_presentation.py

# Run all unit tests
python3 -m unittest discover -s tests
```
