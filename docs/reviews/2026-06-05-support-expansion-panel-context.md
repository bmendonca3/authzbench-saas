# Context Packet: Support Expansion And Goal Refresh

Repository: `https://github.com/bmendonca3/authzbench-saas`

AuthZBench-SaaS is an alpha/pre-v0 benchmark preview. The project goal is to
become a top benchmark for evaluating whether AI agents can prove SaaS
authorization failures without inventing findings.

## Current Public Split

- 3 synthetic Dockerized SaaS apps: `project_mgmt`, `billing`, and `support`
- 21 public tasks
- 9 vulnerable tasks
- 12 secure-control tasks
- covered classes: BOLA, BFLA, invite abuse, and secure controls
- deterministic scorer-owned replay transcripts
- target-side request logs and runner-side per-task request-log correlation in
  alpha form
- no private holdouts committed

## Current Slice Under Review

This slice adds:

- `apps/support/`: a support-ticket SaaS target on port `8013`
- six support tasks:
  - cross-organization ticket read
  - viewer status-write BFLA
  - agent-created admin invite abuse
  - matching secure controls for each case
- scorer support for replaying request bodies in secure controls
- scripted baseline support for the three vulnerable support tasks
- docs/roadmap updates that define the project goal, SDLC checkpoints, and v0
  release gates
- infographic count updates from 15 tasks / 2 apps to 21 tasks / 3 apps

## Files To Inspect

- `docs/goal.md`
- `ROADMAP.md`
- `docs/v0-release-plan.md`
- `README.md`
- `assets/authzbench-saas-infographic.svg`
- `apps/support/app.py`
- `tasks/support/*.json`
- `authzbench/score.py`
- `scripts/scripted_baseline_agent.py`
- `tests/test_http_apps.py`
- `tests/test_harness.py`
- `tests/test_runner.py`
- `tests/test_validate_manifests.py`

## Known Limits

- This remains alpha/pre-v0, not a finished leaderboard.
- The 21-task public split is still small.
- Kiro no-tools model snapshots are legacy 15-task alpha snapshots until rerun.
- Docker smoke can only pass when a Docker daemon is available.
- Private holdouts, multi-seed scoring, broader route aliases/decoys, CI, and
  repeated model baselines are still v0 work.

## Review Questions

1. Does the support app add meaningful benchmark coverage, or is it too similar
   to existing BOLA/BFLA tasks?
2. Are the new secure controls credible false-positive traps?
3. Does request-body replay in controls create scoring risk or improve fidelity?
4. Does `docs/goal.md` make the top-benchmark ambition concrete without
   overclaiming current maturity?
5. Does the roadmap now describe a credible SDLC/review rhythm?
6. What must be verified locally before this checkpoint is committed?
