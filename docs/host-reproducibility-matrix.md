# Host Reproducibility Matrix

This matrix tracks the validation statuses, commands, and host actions for each evaluation layer in the AuthZBench-SaaS host packet.

| Surface | Command / Evidence | Status / Last Checked UTC | Checked By | Environment (OS/Python) | Re-run Command / Failure Action |
| --- | --- | --- | --- | --- | --- |
| **Public Validation** | `python3 scripts/validate_public.py --include-scripted-baseline` | `2026-06-16 15:10 UTC` | Maintainer | macOS / Python 3.11 | `python3 scripts/validate_public.py --include-scripted-baseline` / Fail on errors |
| **Full CI Validation** | GitHub Actions Run ID: `27628002930` | Passing at commit `52e7bda` | CI Runner | Ubuntu / Python 3.11 | Inspect Actions logs / Fail on CI failures |
| **Container Smoke** | `--include-container-smoke` | Passing in CI (Run `27628002930`) | CI Runner | Ubuntu / Python 3.11 (with Docker) | Check containerized logs / Fail on Docker errors |
| **Host-Presentation** | `python3 scripts/validate_host_presentation.py` | `2026-06-16 15:10 UTC` | Maintainer | macOS / Python 3.11 | `python3 scripts/validate_host_presentation.py` / Fail on link or template mismatch |
| **Review Bundle Check** | `python3 scripts/build_host_review_bundle.py --check` | `2026-06-16 15:10 UTC` | Maintainer | macOS / Python 3.11 | `python3 scripts/build_host_review_bundle.py --check` / Regenerate manifest if out of sync |
| **Public Sample CSV** | `python3 scripts/validate_kaggle_sample_submission.py` | `2026-06-16 15:10 UTC` | Maintainer | macOS / Python 3.11 | `python3 scripts/validate_kaggle_sample_submission.py` / Fix format mismatch |
| **Dry-Run Bundle** | `python3 scripts/validate_kaggle_dry_run_bundle.py` | `2026-06-16 15:10 UTC` | Maintainer | macOS / Python 3.11 | `python3 scripts/validate_kaggle_dry_run_bundle.py` / Check dry-run files |
| **Private Holdout Custody** | active/shadow count and fingerprint summaries | Summarized in `docs/privacy-and-holdout-custody.md` | Maintainer | Not applicable | Review custody boundary / Check manifest.json |
| **Host Model** | Model A + Model B (Model C deferred) | Decision recorded in hosting memo | Maintainer | Not applicable | Host accepts or changes proposal |

## Latest CI Verification Reference
- **Latest Verified Commit**: `52e7bda3468d01d0a625d1db43b34191ede5c4b3`
- **Actions Workflow Run ID**: `27628002930`
- **Actions Run URL**: https://github.com/bmendonca3/authzbench-saas/actions/runs/27628002930
- **Conclusion**: `success`
