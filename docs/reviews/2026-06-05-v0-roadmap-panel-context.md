# Context Packet

AuthZBench-SaaS is currently public at:

`https://github.com/bmendonca3/authzbench-saas`

Current alpha preview facts:

- 2 synthetic Dockerized SaaS apps
- 15 public tasks
- 6 vulnerable tasks
- 9 secure-control tasks
- deterministic scorer replay transcripts
- seeded tenant/object/org/invoice/token IDs
- scripted, live HTTP scripted, and two Kiro no-tools baseline summaries

Latest user direction:

- include a repo roadmap
- be thorough and organized
- verify the work with a sectional panel review
- commit at sensible SDLC checkpoints
- make the benchmark trajectory strong enough to become a top benchmark
- keep the current release honest as alpha/pre-v0, not a finished v0

Parent changes prepared for review:

- `README.md` now describes the repo as alpha/pre-v0 and links to the v0 plan.
- `ROADMAP.md` defines milestones from alpha stabilization through v1 candidate.
- `docs/v0-release-plan.md` defines v0 scope, task mix, anti-gaming, live-target
  proof, baseline plan, docs, and release gates.
- `docs/launch-report.md`, `docs/status.md`, `docs/methodology.md`,
  `docs/leaderboard-schema.md`, and `docs/publish-checklist.md` were adjusted
  away from premature v0 framing.

Known current limits:

- no private holdout tasks are public or tracked
- route aliases and decoys are planned but not implemented
- live-target request logging is planned but not implemented
- model baselines are initial and sparse
- CI is not present yet
