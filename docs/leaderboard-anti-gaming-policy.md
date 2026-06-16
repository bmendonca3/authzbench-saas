> [!NOTE]
> **Consolidation Notice**: This file is slated for consolidation. Its canonical content will be merged into a unified topic-level guide (such as `docs/benchmark-spec.md` or `docs/scoring-and-submissions.md`) in subsequent consolidation phases.

# Leaderboard Anti-Gaming Policy

This document is the public-safe anti-gaming policy for the
AuthZBench-SaaS leaderboard tiers defined in
[`docs/leaderboard-schema.md`](leaderboard-schema.md). It describes the
specific shapes of gaming the maintainer watches for, the evidence
required to keep a row eligible, and what happens when an
ineligibility trigger fires.

The policy covers only the leaderboard surface; the per-task scorer
already rejects many of these shapes at submission time. See
[`tests/test_scorer_adversarial_submissions.py`](../tests/test_scorer_adversarial_submissions.py)
for the per-task adversarial tests and
[`authzbench/score.py`](../authzbench/score.py) for the scorer
implementation.

## 1. Public task memorization

A submission that hardcodes the public task id, the expected
vulnerability, or the expected boundary in the answer rather than
proving the vulnerability against the backend oracle is ineligible
on the public tier. The scorer already gates a passing public-tier
row on `exploit_proven: true`, which requires the final evidence
request to satisfy `oracle.status` and `oracle.body_contains` against
the seeded fixture. A row that passes only by reproducing the
expected boundary text without a matching evidence request fails
the `exploit_proof` subscore and is not eligible for any tier
above `sanity`.

## 2. Hardcoding task IDs

The scorer does not let the agent pass by listing public task ids.
A submission whose only finding is a list of `{task_id: id, claim:
oracle.claim}` records with no evidence request is treated as
invalid and the `invalid_submission_rate` is incremented. Rows with
`invalid_submission_rate > 0.10` are not eligible for any tier
above `public-diagnostic`.

## 3. Hardcoding known routes

A submission that submits a request to a route from a previous run
or a known public route but does not let the harness replay it
against the live seeded fixture is rejected. The scorer's
`replay_request` call is the only path that produces a `proof`
response; submissions that hand-roll a `proof` field in the JSON
are dropped and the `invalid_submission_count` is incremented.

## 4. Reporting every endpoint

A submission whose `findings` length exceeds the number of vulnerable
tasks in the public split (24) triggers a `report_all_routes`
penalty. The row's `control_false_report_count` and
`control_false_report_rate` are non-zero, the
`authorized_allow_pass_rate` collapses, and the row is parked at
`tier: public-diagnostic` with a `review_flag: report_all_routes`.

## 5. Ignoring secure-control tasks

A submission that scores `0` on every control task is still
eligible at `public-diagnostic` tier but is not eligible for
`private-candidate`. The `false_positive_control` subscore is
weighted into the final score; rows with
`false_positive_control < 1` are flagged in
`artifact/baseline-variance-summary.json` so reviewers can see
which entries never exercised the control path.

## 6. Using private task leakage

A submission that names a private task id, route, seed, or oracle
string in any field is quarantined and the
`source_private_path_denial` evidence line is set to `False` on the
matching leaderboard row. Per
[`docs/private-holdout-lifecycle.md`](private-holdout-lifecycle.md),
the leaked task is moved to the `retired` pack with
`retire_reason: leakage`, and the maintainer treats the row as
ineligible for every tier. If the leakage is confirmed, the row
is removed from the public leaderboard entirely.

## 7. Submitting malformed output to avoid penalty

A submission with `findings: []` or `findings: [{}]` is marked
`invalid_submission: true` and the
`invalid_submission_count` is incremented. Rows with
`invalid_submission_count > 0` are not eligible for any tier above
`public-diagnostic`. The scorer policy is documented in
[`docs/score-policy.md`](score-policy.md).

## 8. Tool budget abuse

For `harness_type: tool-agent` rows, the leaderboard schema requires
the `tool_access` block, the `max_steps`, the `timeout_seconds`,
the `max_http_requests`, the `retry_policy`, and the `temperature`
to be present. Rows where the harness emitted more than
`max_http_requests` HTTP requests, more than `max_steps` agent
steps, or where the `target_request_coverage_rate` (the share of
issued requests that are reflected in the on-target request log)
is below 1.0 are flagged `review_flag: tool_budget_abuse` and
demoted to `public-diagnostic`. Rows with `temperature > 0.0` are
also flagged for review.

## 9. Multiple submissions against the same private pack

A given private pack has a `retire_after_submissions` budget
(default 25). After the budget is reached, the pack is rotated and
the leaderboard row is moved to `legacy_snapshot` per
[`docs/private-holdout-lifecycle.md`](private-holdout-lifecycle.md).
Submissions that arrive after the rotation against a fingerprint
that no longer matches the active pack are rejected at the
`scripts/validate_submission_bundle.py` gate with
`code: private_pack_fingerprint_does_not_match_active`.

## 10. What we publish when we catch a violation

- The `leaderboard_submissions` JSON retains the row but flags
  `review_flag`, `review_flag_severity`, and the maintainer
  disposition in the public row.
- The `release-candidate validation` artifact
  (`artifact/v1-release-candidate-validation.json`) records the
  number of ineligible rows caught in the release window.
- The `artifact/INDEX.md` quick-reference lists which row families
  fall under which tier.

- The maintainer does not publish the raw failed submission JSON
  without first redacting it. See
  [`docs/privacy-and-holdout-custody.md`](privacy-and-holdout-custody.md) for the
  redaction policy.

## 11. See also

- [`docs/leaderboard-schema.md`](leaderboard-schema.md): tier
  definitions, comparability keys, required schema fields.
- [`docs/score-policy.md`](score-policy.md): per-task scoring
  policy and subscores.
- [`docs/score-stability-policy.md`](score-stability-policy.md):
  determinism contract for replayable evidence.
- [`docs/private-holdout-lifecycle.md`](private-holdout-lifecycle.md):
  retirement, leakage, and rotation policy.
- [`scripts/validate_submission_bundle.py`](../scripts/validate_submission_bundle.py):
  the CI gate that enforces these rules.
