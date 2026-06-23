# Goal And Roadmap Panel Summary

Date: 2026-06-05

Section reviewed:

- `docs/goal.md`
- `ROADMAP.md`
- `docs/v0-release-plan.md`
- `docs/v0-task-build-matrix.md`

Question:

Does the public goal and roadmap make AuthZBench-SaaS more credible as a future
top benchmark while avoiding overclaiming the current alpha/pre-v0 state?

## Reviewer Coverage

Verified reviewer outputs:

- Gemini 3.5 Flash (High)
- Gemini 3.1 Pro (High)
- panel reviewer

Unavailable or limited reviewers:

- Claude Sonnet 4.6 (Thinking): model label was verified, but the output file
  was empty.
- Claude Opus 4.6 (Thinking): model label was verified, but the output file was
  empty.
- Kiro CLI `claude-opus-4.8`: model was available and read-only file access
  started, but the wrapper did not return a clean final review before cleanup.

Raw panel logs are intentionally not committed.

## Accepted Findings

### Secure-control math was inconsistent

Reviewers found that the v0 plan required at least 40 percent secure controls
but also said "at least 25 secure controls" for an approximately 70-task target.
That would be below the stated 40 percent threshold.

Disposition:

- Updated `docs/v0-release-plan.md` to require at least 28 total secure
  controls, counting both denial controls and authorized-allow controls.
- Updated `docs/v0-task-build-matrix.md` to show a concrete 70-task target with
  30 total controls and 12 authorized-allow controls.

### v0 app target was too loose

Reviewers noted that the roadmap and goal used "5-6 apps" even though the build
matrix already targets the existing five apps plus `audit/settings`.

Disposition:

- Updated `docs/goal.md`, `ROADMAP.md`, and `docs/v0-release-plan.md` to use a
  firm 6-app v0 target.

### App naming was inconsistent

Reviewers found that the v0 release plan listed `Invites and membership` as a
separate app while the build matrix uses the existing `support` app plus the new
`audit/settings` app.

Disposition:

- Updated the release-plan app table to use `Support` for ticket ownership,
  status writes, and invite scope.

### Review section names did not match everywhere

Reviewers found that the goal, roadmap, and release gates used slightly
different names for the same sectional reviews.

Disposition:

- Standardized the review section list around goal/roadmap/release criteria,
  task realism and vulnerability/control mix, scorer/runner/request-log/live
  proof, baseline methodology and leaderboard schema, holdout/contamination/
  anti-gaming, and privacy/packaging/final readiness.

### v0 goal checklist omitted some release blockers

Reviewers found that the v0 goal list did not explicitly include CI, live Docker
validation, and fresh public-clone validation, even though those are release
gates elsewhere.

Disposition:

- Added CI, live Docker validation, and fresh public-clone validation to
  `docs/goal.md`.

### Alpha capability table understated completed prototype work

Reviewers found that the v0 release-plan table described the alpha state as only
seeded IDs and replayable requests, while the roadmap already claims prototype
route aliases, decoys, and target logs.

Disposition:

- Updated the alpha table to say prototype target logs, route aliases, and
  decoys are present.

### Public docs included an unnecessary maintainer handle

One reviewer flagged the public docs' explicit maintainer handle as unnecessary
for the goal contract.

Disposition:

- Replaced the handle with "configured maintainer author identity" in
  `docs/goal.md`.

## Rejected Or Deferred Findings

### Expand the build matrix even further

One reviewer suggested a more detailed public/private per-app breakdown. This
was accepted in compact form, but a deeper implementation plan remains deferred
until the next task-design pass.

### Add automated holdout leak prevention hooks now

Reviewers noted that documentation alone cannot prevent private holdout leakage.
This is valid, but it is outside this docs-only checkpoint. The roadmap already
keeps holdout protection and release-readiness validation as v0 hardening work.

## Remaining Risks

- Docker runtime smoke was not part of this section review.
- CI is still planned, not implemented.
- Private holdouts do not exist in the public repo and still need a protected
  execution path.
- Legacy model baselines need reruns after the expanded 37-task public split.
- The current repo remains alpha/pre-v0.
