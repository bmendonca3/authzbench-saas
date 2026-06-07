# Post-v0 Research Artifact Checklist

Status: post-`v0.0` planning checklist.

AuthZBench-SaaS `v0.0` is frozen at the released tag. Work on this branch should
improve research readability, reproducibility, and future v1 planning without
rewriting the released `v0.0` claim boundary.

## Current Claim Boundary

- [x] `v0.0` is a released benchmark artifact.
- [x] The public split remains 46 tasks across 6 synthetic SaaS apps.
- [x] Public baselines are diagnostic public-split evidence, not private model
      rankings.
- [x] Private holdout bodies, raw results, captures, and raw review logs are not
      public artifacts.
- [ ] Hosted leaderboard readiness is intentionally not claimed.
- [ ] v1/community-scale maturity is intentionally not claimed.
- [ ] Production vulnerability-discovery capability is intentionally not
      claimed.

## Paper And Report Tasks

- [x] Create an IEEE-style paper scaffold under `paper/ieee-sp/`.
- [x] Reuse the existing v0.0 technical report and evidence map as the first
      paper source.
- [x] Add paper sections for ethics, open science, limitations, and LLM usage.
- [x] Add a related-work bibliography skeleton.
- [x] Generate paper tables from repository artifacts rather than hand-edited
      claims.
- [ ] Expand the related-work prose into a submission-quality section.
- [ ] Add reviewer calibration notes after external review.

## v1 Benchmark Tasks

- [x] Add `docs/v1-task-expansion-plan.md`.
- [ ] Expand toward 100+ total tasks without weakening secure controls.
- [ ] Add more state-changing workflows across billing, support, file sharing,
      API tokens, and audit/settings.
- [ ] Rerun stale 46-task baselines after any task or scoring change.
- [ ] Keep old baselines clearly marked stale whenever task counts or scoring
      semantics change.

## Leaderboard And Artifact Tasks

- [x] Preserve the existing leaderboard schema and holdout-rotation docs as the
      current source of truth.
- [x] Add an artifact packet scaffold under `artifact/`.
- [ ] Add expected-output fixtures after the public validation packet is frozen.
- [ ] Add signed or attestable run-bundle guidance.
- [ ] Add hosted or fully containerized submission operation only when the
      governance model exists.

## Review And Variance Tasks

- [x] Add `docs/baseline-variance-analysis.md`.
- [x] Add `docs/reviews/external-review-summary.md`.
- [ ] Fill variance analysis from repeated current baseline artifacts.
- [ ] Obtain external appsec review.
- [ ] Obtain external benchmark/evals review.
- [ ] Obtain external AI-agent/tooling review.

## Spot-check Sources

These files should stay consistent with this checklist before any
release-style or paper-submission claim:

- `README.md`
- `ROADMAP.md`
- `docs/status.md`
- `docs/benchmark-card.md`
- `docs/evidence-and-claims.md`
- `docs/release-evidence.json`

## Verification Commands

Run these before making a serious release-style claim:

```bash
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/validate_v0_release.py
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_leaderboard_submission.py --submission 'leaderboard_submissions/**/*.json' --require-source-summary
git diff --check
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs
```

If the LaTeX toolchain is available, also run:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error paper/ieee-sp/main.tex
```
