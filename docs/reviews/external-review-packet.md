# External Review Packet

Status: ready-to-send packet for independent reviewers. No external review is
claimed until findings or explicit no-finding dispositions are recorded in
`docs/reviews/external-review-summary.md`.

## Review Lanes

AuthZBench-SaaS needs three independent review lanes before stronger v1 or
community-benchmark claims are fair:

- Application security: task realism, BOLA/BFLA quality, role/scope/sharing
  boundary quality, and false-positive controls.
- Benchmark/evals methodology: split design, scoring semantics, variance
  framing, stale/current evidence separation, and paper claim boundary.
- AI-agent/tooling: harness assumptions, tool access, live HTTP request
  correlation, agent comparability, and run-bundle evidence.

## Evidence To Send

Use public-safe artifacts only:

- `README.md`
- `ROADMAP.md`
- `docs/benchmark-card.md`
- `docs/evidence-and-claims.md`
- `docs/methodology.md`
- `docs/score-policy.md`
- `docs/result-schema.md`
- `docs/leaderboard-schema.md`
- `docs/task-quality-rubric.md`
- `docs/task-quality-matrix.md`
- `docs/baseline-credibility.md`
- `docs/baseline-variance-analysis.md`
- `docs/boundary-reasoning-calibration-study.md`
- `docs/v1-community-submission-governance.md`
- `docs/authzbench-saas-v1-prep-technical-report.md`
- `baselines/baseline-registry.json`
- public-safe baseline summaries under `baselines/`
- generated charts under `docs/assets/benchmark-charts/`

Do not send private holdout manifests, raw private results, raw captures,
private routes, private seeds, reviewer logs, credentials, local absolute paths,
or ignored run bundles.

## Reviewer Questions

### Application Security

- Do public tasks resemble recognizable SaaS authorization boundaries?
- Are vulnerable tasks paired with meaningful denial or authorized-allow
  controls?
- Which task family is weakest, most ambiguous, or easiest to game?
- Are task descriptions safe enough for public release while still useful for
  benchmark evaluation?
- Would any boundary key or expected behavior confuse a human AppSec reviewer?

### Benchmark And Evals

- Does the evidence support the stated claim boundary?
- Are public-split diagnostics separated from private-holdout leaderboard
  claims?
- Are repeated-run ranges presented as descriptive evidence rather than
  statistical certainty?
- Are stale baselines and current v1-prep baselines separated clearly?
- Does the score policy overreward exploit proof, underweight false positives,
  or hide invalid submissions?

### AI-Agent And Tooling

- Are no-tools model baselines and live HTTP tool-agent baselines compared only
  where comparison is fair?
- Is target-request correlation useful and bounded correctly?
- Are model labels, harness type, tool access, timeouts, benchmark fingerprint,
  and run provenance sufficient?
- Does the boundary-calibration study distinguish model reasoning failures from
  schema or scorer brittleness?
- What artifact would make agent comparability easier to inspect?

## Acceptance Criteria

Each lane is complete only when the public summary records:

- reviewer role and scope;
- review date;
- artifacts reviewed;
- findings or explicit no-finding disposition;
- accepted, rejected, or unresolved decision for each finding;
- follow-up artifact path or issue reference for accepted and unresolved items;
- claim-boundary impact, if any.

Reviewer identity may remain private unless the reviewer grants permission.
