# v1 Readiness Hardening History

Status: historical checkpoint log for public repo-side v1-prep hardening on
2026-06-08. This file preserves detailed commit and CI context so
`docs/goal.md` can stay readable for external reviewers.

## Summary

The public repo-side preparation hardened validator contracts, blocker evidence,
runbooks, templates, reviewer intake, and branch/PR hygiene. These changes make
the remaining v1 gates more explicit, but they do not close external review,
private holdout, hosted/private execution, repeated private evidence, task
scale, paper readiness, or final release-candidate validation.

## Checkpoints

- PR #2 (`fix/live-bearer-auth-parity`) was closed as superseded. The
  Bearer-auth fixture work landed through merged PR #8
  (`fix/live-bearer-auth-parity-bm`). No local worktree or local branch remains
  for the superseded branch, and the stale local No-Mistakes gate ref was
  removed after confirming the worktree was clean.
- Commit `fd461390bd2816ccb8f36d9a3a1979d3ded3ec64` hardened the
  external-review evidence contract so completed lanes must record concrete
  bounded questions reviewed and per-decision summaries. Exact-head GitHub
  Actions run `27122244154` passed on that commit.
- Commit `d74bf2af9e3148e7872a337652baf166864e0636` hardened the final
  release-candidate evidence contract so strict release evidence must record
  workflow name `Validate AuthZBench-SaaS` alongside exact-head CI run ID, URL,
  conclusion, and head SHA. Exact-head GitHub Actions run `27124203762` passed
  on that commit.
- Release-evidence placeholder hardening ensures a copied template cannot pass
  after only changing the schema version. Angle-bracket placeholders are
  rejected in release SHA, benchmark source SHA, private-pack fingerprint, and
  per-command evidence fields.
- Hosted-smoke placeholder hardening ensures a copied release-candidate smoke
  template cannot pass after only changing the schema version. Angle-bracket
  placeholders are rejected in runner/version, private-pack version, isolation
  model, and command fields, including embedded placeholders such as
  `runner:<digest>` or `--private-pack <active-pack>`.
- Private-rotation metadata hardening requires declared pack versions, declared
  SHA-256 fingerprints matching computed pack fingerprints, compatibility
  policy, retirement triggers, and rerun policy before an active plus
  shadow/candidate rotation can pass.
- Paper-readiness evidence hardening requires final release-candidate paper
  evidence to include the exact table, chart, and `latexmk` verification
  commands plus concrete LaTeX result and verification date, rather than
  relying on booleans alone.
- Public blocker evidence refreshes recorded hosted-smoke and private-operation
  blockers as prior-public-checkpoint evidence while keeping both gates red
  because release-candidate private inputs are absent.
- Public blocker reference-scope hardening requires both public blocker records
  to declare `reference_scope: prior_public_checkpoint`, so historical public CI
  references cannot be mistaken for release-candidate or exact-head private
  evidence.
- External-review embedded-placeholder hardening ensures completed or pending
  review lane fields cannot pass with unresolved text such as `TBD`, `TODO`,
  `unknown`, `n/a`, or `<review-artifact>` embedded inside otherwise non-empty
  reviewer questions, artifacts, decisions, or next actions.
- Containerized-submission smoke image hardening ensures exact-head CI does not
  depend on a preloaded `python:3.11-alpine` image: the smoke resolves the
  runner image identity after pulling the image when local Docker inspection
  reports it missing.
- The release-candidate validation contract requires the public-view v1
  readiness fixture check as a recorded release command, so final release
  evidence must prove the tracked clean-clone readiness JSON still matches
  `artifact/expected-output/v1-readiness-public-view.json`.
- The private-operation runbook carries validator-enforced public-safe command
  templates for active/shadow holdout-pack validation, protected-private
  evidence validation, strict release-evidence validation, and the
  tracked-private-path privacy scan, while still remaining runbook evidence
  only.
- The external-review packet includes a validator-required public-safe reviewer
  intake form, so reviewers have a human-facing response shape that maps to the
  structured summary without exposing private identity or private holdout
  details.
- Strict v1 readiness correctly reports `v1_ready: false` because the
  external-review, private-operation, scale, paper, and release-candidate
  evidence gates remain open.
