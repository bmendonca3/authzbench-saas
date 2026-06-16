# Artifact Index

Public-safe artifacts live under `artifact/`. This index is the
quick-reference for reviewers; the long-form descriptions stay in
[`docs/artifact-index.md`](../docs/artifact-index.md).

| Artifact | Purpose | Current / stale | Supports claim | Does not support |
| --- | --- | --- | --- | --- |
| `v1-release-candidate-validation.json` | v1 release-candidate evidence pinned to the CI-validated commit and active private pack fingerprint | current | internal/non-external v1 release-candidate | external acceptance |
| `v1-readiness-public-view.json` (under `expected-output/`) | public-view v1 readiness fixture (`v1_ready: true` is internal/public-view only) | current | internal/public-view readiness gates | external acceptance |
| `baseline-variance-summary.json` | per-cohort mean / std_dev / 95% CI / per-task agreement for every registry entry | current | n=2 repeated-run variance signal | leaderboard-grade public comparison |
| `task-oracle-audit.json` | per-task oracle / boundary / control-mix audit + risk flags | current | schema gate, completeness audit | human realism review |
| `task-taxonomy.json` | per-task vulnerability class / boundary type / control type / route pattern / difficulty classification | current | diversity visibility, gap spotting | semantic accuracy of each label |
| `harbor-adapter-smoke.json` | local Harbor adapter smoke evidence | current | local adapter works on a small public set | Harbor platform acceptance |
| `harbor-parity-experiment.json` | Harbor parity experiment, historical aggregate means | historical | historical aggregate parity | current per-task parity |
| `harbor-adapter-readiness-blockers.json` | explicit blockers for Harbor / platform acceptance | current | current readiness gap | readiness claim |
| `private-holdout-active-public-summary.json` | active private holdout pack public summary | current | count + fingerprint of active pack | per-task private contents |
| `private-holdout-shadow-public-summary.json` | shadow private holdout pack public summary | current | rotation evidence | active pack contents |
| `private-holdout-operation-blocker.json` | explicit blockers for maintainer-operated private runs | current | operational gap | operational claim |
| `submission-runner-smoke.json` | local submission runner smoke (the gate the readiness fixture calls `local_or_containerized_submission_smoke`) | current | local/containerized smoke | hosted leaderboard operation |
| `hosted-submission-execution-runbook.json` | maintainer-platform hosted submission runbook | current | procedural evidence | hosted smoke evidence |
| `expected-output/v1-readiness-public-view.json` | the public-view fixture that CI compares against | current | public-view readiness gate parity | release candidate |
| `task-quality-gate-contract.json` | public-safe acceptance contract for task quality gate | current | schema gate | realism validation |

## Generation

- `baseline-variance-summary.json` and `docs/baseline-variance-analysis.md` are
  produced by `python3 scripts/analyze_baseline_variance.py`. The CI
  `--require-current-public` mode fails when the current-model or
  current-tool-agent cohort is empty.
- `task-oracle-audit.json` and `docs/task-oracle-audit.md` are produced by
  `python3 scripts/generate_task_oracle_audit.py`. The CI `--check` mode
  fails on schema-level gaps (no objective, no oracle, no controls,
  vulnerable task missing denial control).
- `task-taxonomy.json` and `docs/task-taxonomy.md` are produced by
  `python3 scripts/generate_task_taxonomy.py`. The classifier is
  keyword-based; treat the matrix as a starting point for review, not
  a final taxonomy.

## Scope reminders

- Public artifacts must not contain per-task private holdout data,
  raw per-request transcripts of private runs, or real-SaaS credentials.
  See `docs/privacy-scan-rules.md` and `artifact/run-bundle.md` for
  redaction policy.
- The `v1_ready: true` field is **not** a hosted-leaderboard claim and
  must not be paraphrased as "v1 released", "externally validated", or
  "community benchmark". See `docs/claims-and-evidence.md` for the
  canonical claim ledger and the CI-enforced forbidden-phrase list at
  `scripts/check_claim_boundary.py`.
