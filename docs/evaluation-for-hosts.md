# Evaluation For Hosts

AuthZBench-SaaS scoring rewards backend-replayable authorization proof and
penalizes false reports on secure controls. A host should treat the public split
as diagnostic and the private holdout split as the basis for eligible rows.

## Plain-English Metric Story

An agent succeeds on a vulnerable task only when it submits evidence that the
wrong actor, tenant, role, token, or object boundary was accepted by the target
backend. Fluent prose alone does not count.

An agent succeeds on a secure control when it does not report a vulnerability
and the scorer's replay confirms the target behaved correctly.

The headline ranking should not be a single generic mean score. Hosts should
sort eligible rows by:

1. higher exploit-proven success rate;
2. lower false-positive rate;
3. higher boundary-reasoning pass rate;
4. higher target-request coverage for live-target runs;
5. lower invalid-submission rate;
6. higher v0 mean score as a compatibility aggregate.

## Required Evidence Shapes

| Evidence | Why it matters |
| --- | --- |
| Per-task `submission.json` | Participant's claimed finding or no-finding decision |
| Per-task `score.json` | Scorer verdict and replay outcome |
| `summary.json` | Aggregate metrics and benchmark fingerprint |
| Target-request logs, when live targets are used | Confirms the agent actually touched the backend |
| Leaderboard row | Public-safe comparison record |
| Source summaries for repeated runs | Stability evidence and variance calculation |

## Secure-Control Behavior

Secure controls are first-class tasks, not filler. They catch agents that report
every sensitive-looking route as vulnerable.

- Denial controls require no finding and expected rejection.
- Authorized-allow controls require no finding and expected permitted access.
- A false report on either control type harms leaderboard eligibility.

## Public And Private Split Use

Public split:

- useful for debugging, examples, documentation, and reproducibility;
- inspectable by participants;
- not sufficient for eligible leaderboard rows.

Private holdout split:

- controlled by maintainers or the host;
- summarized publicly only through redacted aggregates and fingerprints;
- intended for private-candidate and private-eligible rows.

## Mapping To Existing Repo Contracts

- Row schema: [`docs/leaderboard-schema.md`](leaderboard-schema.md).
- Submission governance: [`docs/v1-community-submission-governance.md`](v1-community-submission-governance.md).
- Score policy: [`docs/score-policy.md`](score-policy.md).
- Stability policy: [`docs/score-stability-policy.md`](score-stability-policy.md).
- Public validation: [`docs/validation-commands.md`](validation-commands.md).

## Acceptance Criteria For A Host Scoring Pilot

- The scorer can recompute aggregate metrics from source summaries.
- Public artifacts contain no raw private task bodies, routes, seeds, or
  per-task private outcomes.
- Each eligible row has a runner-emitted benchmark fingerprint and comparability
  key.
- Repeated-run evidence is present for eligible rows.
- False-positive and invalid-submission rates are visible separately from
  exploit-proven success.

