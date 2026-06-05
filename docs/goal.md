# Project Goal

AuthZBench-SaaS aims to become a top benchmark for one specific question:

> Can an AI agent prove real SaaS authorization failures without inventing
> findings when the target is actually safe?

The current repository is an alpha/pre-v0 preview. It is useful for local
integration, task-design review, and early agent comparisons, but it is not yet
a finished leaderboard benchmark.

## What Top Benchmark Means Here

AuthZBench-SaaS should be known for realistic authorization-boundary testing,
not for generic CTF puzzles. A strong benchmark result should mean the agent can
handle users, roles, tenants, organizations, protected objects, API tokens,
secure controls, and replayable backend evidence.

The benchmark should reward agents that:

- prove vulnerable behavior with replayable HTTP-style evidence
- name the correct actor, role, tenant, organization, and object boundary
- avoid reporting findings on secure controls
- distinguish allowed access from broken access control
- stay within the benchmark policy and target scope

The benchmark should penalize agents that:

- guess findings from route names alone
- submit prose without backend proof
- over-report every sensitive endpoint
- rely on memorized public manifests instead of live reasoning
- ignore tenant, role, or token boundaries

## v0 Working Goal

The real `v0` goal is to turn this alpha preview into a release-worthy
authorization benchmark with enough scale, protected holdouts, live-target proof,
and baseline evidence for other researchers to rely on it.

The current execution goal is to move deliberately from a useful public alpha
into a top-benchmark candidate: add realistic SaaS surfaces section by section,
validate each section with local tests plus panel review, preserve a roadmap
that explains the path to v0, and commit at natural SDLC checkpoints so the
history is auditable.

To call the project `v0`, the repo should have:

- 5-6 synthetic SaaS apps
- 40-50 public tasks
- 20-30 private holdout tasks outside public Git history
- at least 40 percent secure controls
- route aliases, decoys, seeded IDs, and multi-seed private holdouts
- target/proxy-side request logs correlated into per-task result artifacts
- repeated baselines across at least five real model or agent families
- one or more tool-equipped agent baselines, not only no-tools model runs
- sectional panel review for roadmap, task design, scoring, baselines, privacy,
  and release readiness
- public docs that clearly separate alpha results, public-split results, and
  private-holdout leaderboard results

Until those gates are met, the honest label is alpha/pre-v0.

## Contribution Rhythm

Development should move through small, auditable SDLC checkpoints:

- scope/design commit for benchmark goal, roadmap, and release criteria
- task/app commits for each new synthetic SaaS surface
- scorer/harness commits for proof, control, logging, and anti-gaming behavior
- docs/baseline commits after verification artifacts are updated
- release-readiness commits after privacy scans, panel review dispositions, and
  fresh-clone validation pass

Each material benchmark section should have a short review artifact under
`docs/reviews/` that records what was reviewed, what changed, and what remains
open. Raw panel logs should stay out of the public repo.
