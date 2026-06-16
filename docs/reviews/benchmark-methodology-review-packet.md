# Benchmark / Evals Methodology Review Packet

This packet is the v2 external-review handoff for an independent
benchmark / evals methodology reviewer. It assumes the reviewer has
read [`docs/claims-and-evidence.md`](../claims-and-evidence.md)
and the
[`docs/reviews/external-review-intake.md`](external-review-intake.md)
intake form.

## Scope

- The public / private split and the holdout lifecycle.
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
- `docs/holdout-rotation-protocol.md`
- `docs/v1-community-submission-governance.md`
- `docs/baseline-credibility.md`
- `docs/baseline-variance-analysis.md` (generated)
- `artifact/baseline-variance-summary.json` (generated)
- `artifact/task-oracle-audit.json` (generated)
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
  "blocking_issues": [],
  "nonblocking_issues": [],
  "comments_public_safe": "..."
}
```

## Submission

Submit the review form to
`docs/reviews/review-registry.json` and a per-lane summary to
`docs/reviews/external-review-summary.md`.
