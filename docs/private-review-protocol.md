# Private Review Protocol (Controlled External Review Mode)

This protocol describes how an external AppSec reviewer can audit the
active and shadow private holdout packs under controlled conditions
without being trusted with raw private task files. It is the v2
external-validation companion to
[`docs/private-holdout-lifecycle.md`](private-holdout-lifecycle.md).

## Eligibility

- Reviewer must be an active AppSec, SaaS-security, or benchmark-evals
  practitioner with verifiable prior work in the area.
- Reviewer must accept the no-redistribution terms in
  [`docs/reviews/external-review-intake.md`](reviews/external-review-intake.md)
  before any controlled review session.
- Reviewer cannot be a current employee of an entity that operates a
  competing hosted benchmark; conflict-of-interest declarations go in
  the same intake doc.

## What the reviewer sees

In a controlled review session the reviewer can:

- Read the active and shadow pack summaries
  (`artifact/private-holdout-active-public-summary.json` and
  `private-holdout-shadow-public-summary.json`) in full.
- Open a controlled-environment task viewer that renders one private
  task at a time. The viewer does not let the reviewer copy raw
  files out; it logs every task id the reviewer inspected.
- Submit a structured review form (see "Review form" below) per task
  and per pack.

The reviewer cannot:

- Receive raw private task files (`tasks_private/.../*.json`).
- See the active pack's seeds, raw oracle strings, or per-task
  transcripts outside the controlled viewer.
- Publish per-task private contents in any form.

## What the reviewer does not see

- Per-task transcripts of previous leaderboard submissions.
- The private-holdout-operation runbook host-side paths.
- The maintainer's local credentials or `authzbench_harbor/` private
  configuration.
- Any other private holdout pack the maintainer is operating outside
  the documented active / shadow / retired lifecycle.

## Review form

Per task, the reviewer submits a structured form with the following
fields. The form schema lives at
`docs/reviews/schemas/appsec-review.schema.json` (and
`evals-review.schema.json`, `agent-tooling-review.schema.json` for the
other two lanes).

```json
{
  "reviewer_role": "AppSec reviewer",
  "review_date": "YYYY-MM-DD",
  "reviewed_commit_sha": "...",
  "pack_id": "active-private-holdout-v1-pack | shadow-private-holdout-v1-pack",
  "task_id": "private-pack-internal-id-only",
  "realistic": 1,
  "oracle_clear": 1,
  "boundary_valid": 1,
  "false_positive_control_meaningful": 1,
  "unsafe_ambiguity": 0,
  "difficulty_estimate": "single-step-obvious | single-step-with-decoy | multi-step-discovery | state-changing | token-scope-reasoning | false-positive-trap-heavy",
  "comments_public_safe": "..."
}
```

The `realistic`, `oracle_clear`, `boundary_valid`,
`false_positive_control_meaningful`, `unsafe_ambiguity` fields are
1-5 ordinal ratings. `unsafe_ambiguity` is inverted: a high rating
means the task wording is unambiguously safe (no out-of-scope
destructive actions, no plausible false-positive reading).

## Public output rules

The public output of a controlled review session is:

- A single `docs/reviews/external-review-summary.md` entry per lane
  per pack, containing the aggregate rating distribution and the
  reviewer's per-pack `overall_disposition` (`accept` /
  `accept_with_minor_changes` / `reject`). No per-task private
  content is reproduced.
- An updated `docs/reviews/review-registry.json` entry with the
  reviewer id, the review date, the reviewed commit SHA, and the
  pack ids that were audited.

Per-task private content stays inside the controlled viewer and is
not republished.

## What counts as a blocking issue

A reviewer should mark a task or pack as `blocking_issue: true` when
any of the following hold:

- The task wording plausibly leads a competent agent to a
  destructive out-of-scope action.
- The oracle is ambiguous such that two reasonable backend-replay
  runs would disagree on pass/fail.
- The boundary check uses a synonym that the task manifest's
  `boundary_aliases` does not cover, and the alias gap is material.
- The control mix is missing a denial control on a vulnerable task
  (caught by `scripts/generate_task_oracle_audit.py --check`).

A single blocking issue on a pack moves the pack to `retired` for
rework; per the lifecycle policy a new shadow pack is prepared
before the active pack is replaced.

## Privacy and safety

- The controlled-environment viewer must run on a host that the
  maintainer controls; the reviewer connects over a short-lived
  credential scoped to the viewer only.
- The reviewer's local notes, screenshots, and chat logs are private
  to the reviewer and the maintainer; the maintainer does not publish
  them.
- If a reviewer believes they have seen per-task private content that
  should be redacted in the public summary, they flag it via the
  `leakage_concern: true` field in the review form, and the
  maintainer treats it as a leakage event per
  `docs/private-holdout-lifecycle.md`.

## See also

- [`docs/private-holdout-lifecycle.md`](private-holdout-lifecycle.md)
- [`docs/reviews/external-review-intake.md`](reviews/external-review-intake.md)
- [`docs/reviews/external-review-summary.md`](reviews/external-review-summary.md)
- [`docs/reviews/review-registry.json`](reviews/review-registry.json)
- [`docs/claims-and-evidence.md`](claims-and-evidence.md#5-deferred-v2-validation-tracks)
