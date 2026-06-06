# v0 Release Wiring Panel Summary

Date: 2026-06-06

## Scope

Review of release-facing wording and evidence wiring before the final `v0.0`
tag candidate. The review covered README, roadmap, release notes,
release-evidence metadata, benchmark-card wording, generated evidence-readiness
chart semantics, and launch-report baseline consistency.

## Reviewers

- Parent maintainer review with local command verification.
- Kiro `claude-opus-4.8` content review. Command execution was blocked inside
  the Kiro review session, so the Kiro review was treated as a content review,
  not an independent validator run.

## Findings and Disposition

- Release notes used shipped-release wording before the tag existed.
  Disposition: fixed by adding a draft/not-yet-tagged banner.
- `docs/launch-report.md` claimed five model/agent families but omitted GLM
  rows from the baseline table and source list.
  Disposition: fixed by adding the two current GLM rows and source links.
- README and release evidence handled the no-hosted-leaderboard boundary
  correctly.
  Disposition: retained and clarified in the README rewrite.
- `docs/release-evidence.json` handled the self-referential commit/CI problem
  honestly by separating the evidence-bearing checkpoint, the latest checked
  head, and the policy that the final tag target must pass post-push CI.
  Disposition: retained.
- No private manifests, raw result bundles, captures, or raw panel logs should
  be tracked.
  Disposition: verify with `git ls-files tasks_private/holdout results captures
  docs/reviews/panel-logs` before commit and again before tagging.

## Decision

The release-facing wording is suitable for a `v0.0` candidate after the fixes
above, provided local validation, privacy checks, fresh-clone validation,
post-push CI, and final tag verification pass on the final pushed commit.

This summary does not authorize hosted leaderboard claims, v1 claims, or private
tool-agent leaderboard eligibility.
