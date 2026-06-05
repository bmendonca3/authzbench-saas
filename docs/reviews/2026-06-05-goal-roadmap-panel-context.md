# Goal And Roadmap Panel Context

Date: 2026-06-05

Section under review: public goal, roadmap, and v0 release-planning docs.

User requirement:

- Rewrite the goal with the new objective: AuthZBench-SaaS should become a top
  benchmark, not merely a small demo.
- Include a roadmap in the repo.
- Require sectional panel review for material benchmark areas.
- Preserve a disciplined SDLC contribution rhythm with commits at meaningful
  checkpoints.
- Keep the current repository honest as alpha/pre-v0 until the v0 gates are met.

Files changed in this section:

- `docs/goal.md`
- `ROADMAP.md`
- `docs/v0-release-plan.md`

Relevant current repo facts:

- Current public state is alpha/pre-v0.
- Public split currently has 5 synthetic SaaS apps and 37 public tasks.
- Current tracked public task mix is 15 vulnerable tasks and 22 secure controls.
- Real v0 still requires private holdouts, stronger anti-gaming, repeated real
  model/agent baselines, live Docker validation, CI, release readiness review,
  and fresh public-clone validation.

Review question:

Does this goal/roadmap section make the project more credible as a future top
benchmark while avoiding overclaiming the current alpha state?

Review criteria:

- The goal should read like an operating contract, not marketing copy.
- The roadmap should be specific enough for contributors to understand the path
  from alpha to v0 and later v1.
- Sectional panel review should be required before release claims, with clear
  minimum sections.
- Commit rhythm should match meaningful SDLC checkpoints.
- The docs should not imply the current repo is already v0, leaderboard-ready,
  or top-tier.
- No personal or private information should appear in the reviewed docs.
