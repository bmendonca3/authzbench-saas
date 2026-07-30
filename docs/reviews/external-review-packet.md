# External Review Packet

Status: local public-safe handoff candidate for independent reviewers (v2
preparation), refreshed from base commit
`acb6434c4bb25cce53a1a9f4eb31c869986743ca` with evidence through
2026-07-28. It has not been sent. Before distribution, freeze the final review
commit and record that exact SHA in every returned review. No external review
is claimed until findings or explicit no-finding dispositions are recorded in
the validated review surfaces.

## Review Lanes

AuthZBench-SaaS needs three independent review lanes to reach its v2/post-v1
credibility goals:

- Application security: task realism, BOLA/BFLA quality, role/scope/sharing
  boundary quality, and false-positive controls.
- Benchmark/evals methodology: split design, scoring semantics, variance
  framing, stale/current evidence separation, and paper claim boundary.
- AI-agent/tooling: harness assumptions, tool access, live HTTP request
  correlation, agent comparability, and run-bundle evidence.

The current public set contains 63 tasks across 6 synthetic SaaS apps:
27 vulnerable tasks and 36 secure controls (21 denial and 15
authorized-allow). Public-safe private summary metadata covers 48 holdout
tasks (24 vulnerable and 24 controls); private task bodies and raw private
evidence are not part of this packet.

The versioned scored-cohort contract is a review candidate, not an accepted
methodology. It maps the 63 public tasks into 17 semantic clusters. Private
cluster assignment and semantic disjointness, minimum discriminating task and
cluster counts, independent methodology approval, cohort admission, and launch
eligibility remain unresolved.

## Evidence To Send

Use public-safe artifacts only:

- `README.md`
- `ROADMAP.md`
- `docs/benchmark-spec.md`
- `docs/claims-and-evidence.md`
- `docs/scoring-and-submissions.md`
- `docs/task-quality-rubric.md`
- `docs/task-quality-matrix.md`
- `docs/baseline-credibility.md`
- `docs/baseline-variance-analysis.md`
- `docs/boundary-reasoning-calibration-study.md`
- `docs/kaggle-benchmark-design-contract.md`
- `docs/v1-community-submission-governance.md`
- `docs/authzbench-saas-v1-prep-technical-report.md`
- `docs/reviews/external-review-intake.md`
- `docs/reviews/appsec-review-packet.md`
- `docs/reviews/benchmark-methodology-review-packet.md`
- `docs/reviews/agent-tooling-review-packet.md`
- `docs/reviews/schemas/appsec-review.schema.json`
- `docs/reviews/schemas/evals-review.schema.json`
- `docs/reviews/schemas/agent-tooling-review.schema.json`
- `docs/reviews/external-review-response.template.json`
- `artifact/scored-cohort-contract.v1.json`
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
- Are stale 44-task, frozen 46-task, historical 49-task, stale 54-task and
  60-task, and current 63-task evidence separated clearly?
- Is it clear that the current 63-task model/tool rows are offline policy-v2
  rescores of saved full-split submissions, not fresh repeated model
  execution under policy v2?
- Does the candidate cohort contract define defensible semantic clusters and
  cluster-disjoint split rules, and what analysis should determine the minimum
  discriminating task and cluster counts?
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

- the exact 40-character reviewed commit SHA shared by every completed lane;
- reviewer role and scope;
- review date;
- bounded questions reviewed;
- artifacts reviewed;
- findings or explicit no-finding disposition;
- accepted, rejected, or unresolved decision for each finding;
- follow-up artifact path or issue reference for accepted and unresolved items;
- claim-boundary impact, if any.

The reviewed SHA must contain the mandatory product source and evidence trees
enforced by `scripts/validate_v2_external_validation.py`; a reviewer-optional
artifact list cannot exempt changed app, scorer, runner, task, test, Harbor,
paper, or generated benchmark inputs. Accepted findings require committed
post-review remediation, and the affected source must receive final review
before strict completion.

Reviewer identity may remain private unless the reviewer grants permission.
Use `docs/reviews/external-review-response.template.json` as the response shape,
then follow the explicit template-to-summary transformation in
`docs/reviews/external-review-intake.md` before updating the canonical
`docs/reviews/external-review-summary.json`. The template is not evidence and
cannot satisfy the external-review gate unchanged. Run
`python3 scripts/validate_v2_external_validation.py --require-complete`; the
validator also rejects
embedded unresolved markers such as `TBD`, `TODO`, `pending`, `unknown`, `n/a`,
and `<placeholder>` in pending or completed review questions, artifacts,
decisions, blockers, next actions, and claim-boundary notes.
