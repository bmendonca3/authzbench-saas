# AppSec Review Packet

This packet is the v2 external-review handoff for an independent
application-security reviewer. It assumes the reviewer has read
[`docs/current-claim-boundary.md`](../current-claim-boundary.md)
and the
[`docs/reviews/external-review-intake.md`](external-review-intake.md)
intake form. The packet does not include private holdout manifests;
private review is conducted under the
[`docs/private-review-protocol.md`](../private-review-protocol.md)
controlled-environment contract.

## Scope

- All 60 public tasks under `tasks/` (6 apps × 10 tasks).
- The active private holdout pack summary
  (`artifact/private-holdout-active-public-summary.json`) at the
  pack level only. Per-task private contents are reviewed under
  `docs/private-review-protocol.md`.
- The task taxonomy (`artifact/task-taxonomy.json`) and oracle
  audit (`artifact/task-oracle-audit.json`).

## Materials

- `docs/task-quality-rubric.md`
- `docs/task-quality-matrix.md`
- `docs/boundary-reasoning-calibration-plan.md`
- `docs/boundary-reasoning-calibration-study.md`
- `docs/task-oracle-audit.md` (generated)
- `docs/task-taxonomy.md` (generated)
- `authzbench/score.py` (the scorer)
- `tests/test_scorer_adversarial_submissions.py` (the adversarial
  test suite the AppSec reviewer can read to see what the scorer
  is contracted to reject)

## Reviewer questions

The reviewer should answer the following for the public split and,
in a separate section, for the active private pack under the
controlled review protocol.

1. **Task realism**: For each task family (BOLA, BFLA, cross-tenant
   read/write, role bypass, token-scope bypass, entitlement bypass,
   stale share-link, reassignment abuse, audit/admin exposure), do
   the public tasks exercise a recognizable SaaS authorization
   boundary, or do they rely on synthetic-only quirks?
2. **Oracle clarity**: Is the `oracle.status` and `oracle.body_contains`
   pair unambiguous enough that two reasonable backend-replay runs
   would agree on pass / fail?
3. **Boundary validity**: For each task with `expected_boundary`, do
   the `boundary_aliases` cover the reviewer-visible synonyms the
   AppSec reviewer would expect, or is there a material gap?
4. **False-positive controls**: For each vulnerable task, does the
   `controls` list include at least one denial control and at least
   one decoy or alias route that would catch an over-reporting agent?
5. **Unsafe ambiguity**: Does any task wording plausibly lead a
   competent agent to a destructive out-of-scope action? Flag the
   task and explain.
6. **Difficulty estimate**: For each task, is the difficulty label
   (single-step obvious / single-step with decoy / multi-step
   discovery / state-changing / token-scope reasoning / false-positive
   trap-heavy) accurate?
7. **AppSec mapping**: Where applicable, what CWE / OWASP entry best
   describes the vulnerability class the task exercises?

## Review form

Per task, the reviewer submits a structured form
(`docs/reviews/schemas/appsec-review.schema.json`) with the
following fields:

```json
{
  "reviewer_role": "AppSec reviewer",
  "review_date": "YYYY-MM-DD",
  "reviewed_commit_sha": "...",
  "pack_id": "public | active-private-holdout-v1-pack | shadow-private-holdout-v1-pack",
  "task_id": "...",
  "realistic": 1,
  "oracle_clear": 1,
  "boundary_valid": 1,
  "false_positive_control_meaningful": 1,
  "unsafe_ambiguity": 0,
  "difficulty_estimate": "single-step-obvious | single-step-with-decoy | multi-step-discovery | state-changing | token-scope-reasoning | false-positive-trap-heavy",
  "cwe_or_owasp_mapping": "CWE-639 | OWASP-API1:2023 | ...",
  "comments_public_safe": "..."
}
```

The `realistic`, `oracle_clear`, `boundary_valid`,
`false_positive_control_meaningful`, `unsafe_ambiguity` fields are
1-5 ordinal ratings. `unsafe_ambiguity` is inverted: a high rating
means the task wording is unambiguously safe (no out-of-scope
destructive actions, no plausible false-positive reading).

## What counts as blocking

A reviewer should mark a task or pack as `blocking_issue: true` when
any of the following hold:

- The task wording plausibly leads a competent agent to a
  destructive out-of-scope action.
- The oracle is ambiguous such that two reasonable backend-replay
  runs would disagree on pass / fail.
- The boundary check uses a synonym that the task manifest's
  `boundary_aliases` does not cover, and the alias gap is material.
- The control mix is missing a denial control on a vulnerable task
  (caught by `scripts/generate_task_oracle_audit.py --check`).

A single blocking issue on a pack moves the pack to `retired` per
[`docs/private-holdout-lifecycle.md`](../private-holdout-lifecycle.md)
for rework.

## Submission

Submit the review form to
`docs/reviews/review-registry.json` and a per-lane summary to
`docs/reviews/external-review-summary.md`. Do not include per-task
private contents.
