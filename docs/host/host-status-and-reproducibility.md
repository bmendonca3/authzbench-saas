# Host Status and Reproducibility Matrix

Status: single-page status and reproducibility summary for Kaggle host reviewers. This page tracks reference hashes, versions, and validation statuses to ensure host packet reproducibility. It does not claim platform acceptance, hosted leaderboard operation, external validation, or third-party submissions.

---

## 1. Current Status

* **Last updated**: 2026-06-23
* **Current commit**: `bba7007e7bac50ac69d32f650e461869228baa1d` on branch `main`
* **Local validation**: `python3 scripts/validate_host_presentation.py` passing

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
| Platform acceptance | Accept or decline to host the benchmark | Kaggle |
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
| **Public Validation** | `python3 scripts/validate_public.py --include-scripted-baseline` | `2026-06-23 21:05 UTC` | Maintainer | macOS / Python 3.11 | `python3 scripts/validate_public.py --include-scripted-baseline` / Fail on errors |
| **Full CI Validation** | GitHub Actions Run ID: `28057052847` | Passing at commit `bba7007` | CI Runner | Ubuntu / Python 3.11 | Inspect Actions logs / Fail on CI failures |
| **Container Smoke** | `--include-container-smoke` | Passing in CI (Run `28057052847`) | CI Runner | Ubuntu / Python 3.11 (with Docker) | Check containerized logs / Fail on Docker errors |
| **Host-Presentation** | `python3 scripts/validate_host_presentation.py` | `2026-06-23 21:05 UTC` | Maintainer | macOS / Python 3.11 | `python3 scripts/validate_host_presentation.py` / Fail on link or template mismatch |
| **Review Bundle Check** | `python3 scripts/build_host_review_bundle.py --check` | `2026-06-23 21:05 UTC` | Maintainer | macOS / Python 3.11 | `python3 scripts/build_host_review_bundle.py --check` / Regenerate manifest if out of sync |
| **Public Sample CSV** | `python3 scripts/validate_kaggle_sample_submission.py` | `2026-06-16 15:10 UTC` | Maintainer | macOS / Python 3.11 | `python3 scripts/validate_kaggle_sample_submission.py` / Fix format mismatch |
| **Dry-Run Bundle** | `python3 scripts/validate_kaggle_dry_run_bundle.py` | `2026-06-16 15:10 UTC` | Maintainer | macOS / Python 3.11 | `python3 scripts/validate_kaggle_dry_run_bundle.py` / Check dry-run files |
| **Private Holdout Custody** | active/shadow count and fingerprint summaries | Summarized in `docs/private-holdout-lifecycle.md` and `docs/host/host-operations-runbook.md` | Maintainer | Not applicable | Review custody boundary / Check manifest.json |
| **Host Model** | Model A + Model B (Model C deferred) | Decision recorded in hosting memo | Maintainer | Not applicable | Host accepts or changes proposal |

### Latest CI Verification Reference
* **Latest Verified Commit**: `bba7007e7bac50ac69d32f650e461869228baa1d`
* **Actions Workflow Run ID**: `28057052847`
* **Actions Run URL**: https://github.com/bmendonca3/authzbench-saas/actions/runs/28057052847
* **Conclusion**: `success`

---

## 5. Host Packet Versioning

### Reference Versions
* **Repository Commit SHA**: `bba7007e7bac50ac69d32f650e461869228baa1d`
* **Actions Workflow Run ID**: `28057052847`
* **Host Review Bundle Manifest SHA-256**: [Generated at build time]
* **Active Private Pack Public-Summary Fingerprint SHA-256**: `6b8b51c03492238c881b737029e7802d4127ab2a53655db2b7d5bf25032ba7c8`

### Citation Format
```bibtex
@misc{authzbench2026saas,
  title={AuthZBench-SaaS: Evidence-Based SaaS Authorization Evaluation},
  author={AuthZBench Team},
  year={2026},
  howpublished={\url{https://github.com/bmendonca3/authzbench-saas}},
  note={Host Review Package Candidate Commit bba7007}
}
```

### Update Policy
This host review packet is tagged and frozen relative to the above candidate commit SHA. Any subsequent changes to tasks, scorers, or rules templates will trigger a new candidate commit and manifest regeneration.

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
