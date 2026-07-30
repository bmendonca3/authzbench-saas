# Benchmark / Evals Methodology Review Packet

This packet is the v2 external-review handoff for an independent
benchmark / evals methodology reviewer. It assumes the reviewer has
read [`docs/claims-and-evidence.md`](../claims-and-evidence.md)
and the
[`docs/reviews/external-review-intake.md`](external-review-intake.md)
intake form.

Status: local public-safe handoff candidate refreshed from base commit
`acb6434c4bb25cce53a1a9f4eb31c869986743ca` with evidence through
2026-07-28. It has not been sent. Freeze and record the final review commit
before an external reviewer starts.

## Scope

- The public / private split and the holdout lifecycle.
- The draft semantic-cluster and scored-cohort contract, including the
  disjointness and minimum-count decision method.
- The scoring policy and the deterministic replay contract.
- The baseline registry, variance report, and release-snapshot
  policy.
- The leaderboard schema, eligibility tiers, and anti-gaming
  policy.
- The claim-boundary enforcement (forbidden-phrase CI check,
  Harbor non-claim test, public-view readiness fixture).

## Materials

- `docs/benchmark-spec.md`
- `docs/scoring-and-submissions.md`
- `docs/score-stability-policy.md`
- `docs/kaggle-benchmark-design-contract.md`
- `docs/holdout-rotation-protocol.md`
- `docs/v1-community-submission-governance.md`
- `docs/baseline-credibility.md`
- `docs/baseline-variance-analysis.md` (generated)
- `artifact/baseline-variance-summary.json` (generated)
- `artifact/task-oracle-audit.json` (generated)
- `artifact/scored-cohort-contract.v1.json`
- `docs/reviews/cohort-methodology-decision.json`
- `docs/reviews/schemas/cohort-methodology-decision.schema.json`
- `artifact/expected-output/v1-readiness-public-view.json`
- `baselines/baseline-registry.json`
- `scripts/check_claim_boundary.py`
- `tests/test_claim_boundary_check.py`
- `tests/test_harbor_claim_boundary.py`

## Reviewer questions

1. **Split design**: Does the public / private split protect against
   memorization while still letting external reviewers audit a
   meaningful share of the benchmark?
2. **Scoring semantics**: Are the subscores (`exploit_proof`,
   `boundary_reasoning`, `false_positive_control`, `safety`) and
   the final weighted score policy documented clearly enough that
   a reviewer can derive the math from the policy and the public
   test fixtures?
3. **Determinism**: Does the scorer's deterministic replay contract
   (see `docs/score-stability-policy.md`) hold for the public tasks
   and the synthetic apps?
4. **Variance framing**: Is the n=2 repeated-run 95% CI clearly
   framed as a coarse ordering signal, not a hard bound? Are the
   small-n warnings visible in `docs/baseline-variance-analysis.md`?
5. **Stale / current separation**: Are historical baselines clearly
   marked `evidence_status: historical_stale` and excluded from
   current comparison?
6. **Leaderboard tiers**: Are the
   `sanity / public-diagnostic / private-candidate / private-eligible / external-verified`
   tiers and the tool-agent comparability keys documented well enough
   that a reviewer can verify which rows are comparable?
7. **Anti-gaming**: Does
   `docs/scoring-and-submissions.md` cover the gaming shapes
   that an evals methodology reviewer would flag (public task
   memorization, hardcoded task ids, known routes, report-all-routes,
   ignored secure controls, private leakage, malformed output, tool
   budget abuse, multiple submissions against the same private pack)?
8. **Claim-boundary enforcement**: Is the forbidden-phrase CI check
   broad enough to catch the wording drift the reviewer would flag?
9. **Scored-cohort design**: Does the draft 17-cluster contract define
   defensible semantic clusters and cluster-disjoint split rules? What
   analysis should determine the minimum discriminating task and cluster
   counts before any cohort is admitted?
10. **Evidence generations**: Are stale 44-task, frozen 46-task, historical
    49-task, stale 54-task and 60-task, and current 63-task evidence separated
    clearly? Is the current 63-task model/tool evidence accurately described
    as offline policy-v2 rescores of saved full-split submissions rather than
    fresh repeated model execution under policy v2?
11. **Private cohort decision**: After controlled private analysis, are the
    aggregate private cluster assignment, exact public/private source
    bindings, semantic disjointness result, and numeric minimum analysis
    sufficient to admit a scored cohort without exposing private task details?

## Review form

```json
{
  "reviewer_role": "Benchmark / evals reviewer",
  "review_date": "YYYY-MM-DD",
  "reviewed_commit_sha": "...",
  "split_design_acceptable": 1,
  "scoring_semantics_clear": 1,
  "determinism_contract_holds": 1,
  "variance_framing_acceptable": 1,
  "stale_current_separation_clear": 1,
  "leaderboard_tiers_acceptable": 1,
  "anti_gaming_policy_acceptable": 1,
  "claim_boundary_enforcement_acceptable": 1,
  "private_cluster_assignment_reviewed": false,
  "public_private_cluster_disjointness_verified": false,
  "minimum_analysis_artifact": "...",
  "minimum_scored_task_count": 1,
  "minimum_semantic_cluster_count": 1,
  "cohort_methodology_decision": "accept | accept_with_minor_changes | reject",
  "blocking_issues": [],
  "nonblocking_issues": [],
  "comments_public_safe": "..."
}
```

## Submission

Submit the review form to
`docs/reviews/external-review-registry.json` and copy the public-safe per-lane
summary into `docs/reviews/external-review-summary.json` and
`docs/reviews/external-review-summary.md`. Do not mark the lane complete until
the registry contains a real reviewer record and the validators accept it.
Separately update `docs/reviews/cohort-methodology-decision.json` only from
public-safe, source-bound aggregate evidence. Structural validation is
`python3 scripts/validate_cohort_methodology_decision.py`; strict acceptance is
`python3 scripts/validate_cohort_methodology_decision.py --require-complete`.
