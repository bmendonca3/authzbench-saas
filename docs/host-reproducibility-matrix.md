# Host Reproducibility Matrix

This matrix tracks the validation statuses, commands, and host actions for each evaluation layer in the AuthZBench-SaaS host packet.

| Surface | Command / Evidence | Current Status | Public-safe? | Host Action / Verification |
| --- | --- | --- | --- | --- |
| **Public Validation** | `python3 scripts/validate_public.py --include-scripted-baseline` | Passing locally | Yes | Host can execute from fresh clone |
| **Full CI Validation** | GitHub Actions Run ID: `27596271507` | Passing at commit `ef8b233` | Yes | Host can inspect Actions logs |
| **Container Smoke** | `--include-container-smoke` | Passing in CI (requires Docker daemon) | Yes | Host can execute locally if Docker is running |
| **Host-Presentation** | `python3 scripts/validate_host_presentation.py` | Passing locally | Yes | Host can verify all links and templates |
| **Review Bundle Check** | `python3 scripts/build_host_review_bundle.py --check` | Passing locally | Yes | Host can verify that the public-safe manifest matches expected template |
| **Public Sample CSV** | `python3 scripts/validate_kaggle_sample_submission.py` | Passing locally | Yes | Host can inspect validation logic |
| **Dry-Run Bundle** | `python3 scripts/validate_kaggle_dry_run_bundle.py` | Passing locally | Yes | Host can inspect dry-run formats |
| **Private Holdout Custody** | active/shadow count and fingerprint summaries | Summarized in `docs/privacy-and-holdout-custody.md` | Yes | Host reviews custody boundary |
| **Host Model** | Model A + Model B (Model C deferred) | Decision recorded in hosting memo | Yes | Host accepts or changes proposal |

## Latest CI Verification Reference
- **Latest Verified Commit**: `ef8b233565bfc1a606bf38b2e9afdd3d60bf4158`
- **Actions Workflow Run ID**: `27596271507`
- **Actions Run URL**: https://github.com/bmendonca3/authzbench-saas/actions/runs/27596271507
- **Conclusion**: `success`
