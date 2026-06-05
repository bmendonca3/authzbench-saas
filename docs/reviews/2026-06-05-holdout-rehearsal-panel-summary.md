# Holdout Rehearsal Workflow Panel Summary

Review date: 2026-06-05

Question: Does the private-holdout rehearsal workflow improve v0 readiness
without misleading users into treating generated rehearsal tasks as real private
leaderboard holdouts?

## Reviewers Counted

- Gemini 3.5 Flash (High), verified from panel log model evidence.
- Gemini 3.1 Pro (High), verified from panel log model evidence.
- Claude Sonnet 4.6 (Thinking), verified from panel log model evidence.
- Claude Opus 4.6 (Thinking), verified from panel log model evidence.
- ChatGPT subagent reviewer.

Kiro `claude-opus-4.8` passed preflight but did not return a usable final
answer within the bounded review window. Its child process was stopped and is
not counted.

Raw Antigravity/Kiro logs were written under ignored
`docs/reviews/panel-logs/` and local Antigravity panel-log paths. They are not
committed.

## Consensus

The holdout rehearsal workflow is alpha-stable for its stated purpose:
maintainers can test the private-pack generation and validation path without
committing private JSON. The workflow should not be treated as real v0 private
leaderboard evidence because it is generated from public task structure.

The reviewers agreed that the docs are generally clear, but found two concrete
hardening issues worth fixing before relying on the section:

- Custom in-repo output paths could include `tasks_private/holdout` in their
  path parts without actually being covered by the repo-root `.gitignore`
  pattern.
- The validator could return `passed: true` for a rehearsal pack without a
  machine-readable warning that the pack is not leaderboard-suitable.

## Accepted Findings And Fixes

- Tightened `scripts/generate_holdout_rehearsal_pack.py` so in-repo writes must
  live under the actual ignored repo-root `tasks_private/holdout/` directory.
- Added `leaderboard_suitable: false` to generated rehearsal manifests.
- Added rehearsal detection, `rehearsal_manifest_count`, warnings, and
  `leaderboard_suitable: false` output to `scripts/validate_holdout_pack.py`
  when rehearsal manifests are present.
- Added a regression test for rejecting in-repo non-ignored custom output paths.
- Updated holdout docs and status docs to mention the machine-readable
  rehearsal warning.

## Rejected Or Deferred Findings

- A separate `split` value such as `rehearsal_holdout` was deferred. The current
  validator supports only `public` and `private_holdout`, and the accepted
  machine-readable `leaderboard_suitable: false` plus rehearsal warnings handle
  the immediate alpha-risk without changing the task schema.
- CI remains a known release gate, but workflow pushes are blocked until the
  GitHub credential has workflow scope. This section was validated locally and
  from a fresh public clone instead.

## Remaining v0 Risk

The section does not satisfy real v0 private-holdout requirements. Real v0 still
needs unpublished human-designed holdout tasks, protected execution that does
not expose readable holdout manifests to participants, repeated real model
baselines, stronger route alias/randomization, and final release-readiness
review.
