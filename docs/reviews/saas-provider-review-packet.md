# SaaS-Provider / Product-Security Review Packet

Status: ready-to-send packet for SaaS-provider or product-security
reviewers. No SaaS-provider validation is claimed until findings or
explicit no-finding dispositions are recorded in
`docs/reviews/external-review-summary.md`.

## Purpose

This packet enables a SaaS product-security team to review whether the
benchmark's task scenarios represent realistic SaaS authorization failure
patterns. The reviewer assesses whether vulnerable tasks mirror real-world
authorization boundaries and whether secure controls are meaningful from a
product-security perspective.

This review lane is distinct from the AppSec review
([`appsec-review-packet.md`](appsec-review-packet.md)) because:

- **AppSec reviewers** evaluate task quality, oracle clarity, and boundary
  validity from a penetration-testing lens.
- **SaaS-provider reviewers** evaluate whether the modeled authorization
  patterns (BOLA, BFLA, cross-tenant, role bypass, token scope, entitlement,
  share-link, reassignment) match real production SaaS authorization
  architectures.

## Scope

- All 60 public tasks under `tasks/` (6 apps × 10 tasks).
- The task taxonomy (`artifact/task-taxonomy.json`) focusing on vulnerability
  family distribution and control type balance.
- The authorization model descriptions in each synthetic SaaS app's README.
- The scorer's replay-based verification model (`authzbench/score.py`).

## Materials

Use public-safe artifacts only:

- `README.md`
- `docs/benchmark-card.md`
- `docs/evidence-and-claims.md`
- `docs/methodology.md`
- `docs/task-taxonomy.md`
- `docs/task-quality-rubric.md`
- `docs/task-quality-matrix.md`
- `docs/current-claim-boundary.md`
- `docs/score-policy.md`
- `docs/scoring-examples.md`
- `artifact/task-taxonomy.json`
- `artifact/task-oracle-audit.json`
- Public task manifests under `tasks/`
- Synthetic SaaS app source under `apps/`

Do not send private holdout manifests, raw private results, raw captures,
private routes, private seeds, reviewer logs, credentials, or ignored run
bundles.

## Reviewer Questions

1. **Authorization model fidelity**: Do the synthetic SaaS apps model
   authorization boundaries (tenant isolation, role hierarchy, scope
   restrictions, sharing policies) in a way that reflects real SaaS
   production architectures?

2. **Vulnerability family coverage**: Does the task taxonomy cover the
   authorization failure families that matter most in production SaaS?
   Which families are missing or underrepresented?

3. **Control realism**: Are the secure-control tasks (denial controls and
   authorized-allow controls) representative of how real SaaS applications
   defend against the modeled vulnerabilities?

4. **Scoring validity**: Does the replay-based scoring model (backend
   HTTP replay verification) adequately distinguish real exploits from
   false positives in a way that a product-security team would trust?

5. **Risk representation**: Are there authorization failure patterns
   common in production SaaS that are materially absent from the
   benchmark, making the benchmark's coverage claims misleading?

6. **Synthetic vs. production gap**: For each app, what aspects of the
   synthetic authorization model diverge most from a real production
   deployment, and does that divergence affect benchmark validity?

7. **Claim-boundary appropriateness**: Given the benchmark's explicit
   non-claims (no SaaS-provider validation, no production deployment
   endorsement), is the claim boundary appropriately conservative?

## Review Form

Per app and per vulnerability family, the reviewer submits a structured
form with the following fields:

```json
{
  "reviewer_role": "SaaS product-security reviewer",
  "review_date": "YYYY-MM-DD",
  "reviewed_commit_sha": "...",
  "app_id": "...",
  "vulnerability_family": "BOLA | BFLA | cross-tenant | role-bypass | token-scope | entitlement | share-link | reassignment | admin-exposure",
  "auth_model_fidelity": 1,
  "control_realism": 1,
  "scoring_validity": 1,
  "coverage_adequacy": 1,
  "synthetic_gap_severity": 1,
  "blocking_issue": false,
  "comments_public_safe": "..."
}
```

The `auth_model_fidelity`, `control_realism`, `scoring_validity`,
`coverage_adequacy` fields are 1–5 ordinal ratings (5 = highest confidence).
`synthetic_gap_severity` is 1–5 where 1 = negligible gap and 5 = the synthetic
model diverges materially from production.

## What Counts as Blocking

A reviewer should mark an app or vulnerability family as
`blocking_issue: true` when:

- The synthetic authorization model is so divergent from production that
  benchmark scores would mislead a real product-security assessment.
- A major authorization failure family (e.g., multi-tenant isolation) is
  absent and the benchmark's coverage claims do not acknowledge this.
- The scoring model would accept a submission that a product-security
  reviewer would reject as a false positive, or vice versa.

## Submission

Submit the review form to `docs/reviews/review-registry.json` and a
per-lane summary to `docs/reviews/external-review-summary.md`. Do not
include per-task private contents.

## Explicit Non-Claims

This packet does not claim SaaS-provider validation, product-security
endorsement, production deployment suitability, or external validation
completion. The benchmark's claim boundary explicitly excludes these claims
until this review lane records findings or a no-finding disposition.
