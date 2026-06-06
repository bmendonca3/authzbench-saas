# Score Stability Policy

AuthZBench-SaaS is alpha/pre-v0, so task and scorer changes are still expected.
This policy keeps old scores understandable when the benchmark changes.

## Score States

| State | Meaning |
| --- | --- |
| `current_public_split` | Run on the current public task set and current scorer profile. |
| `current_public_stale` | Run on a recently superseded public task set; useful context, but rerun required before current comparison or v0 claims. |
| `current_private_holdout` | Maintainer-side private holdout run for release-candidate evidence. |
| `legacy_snapshot` | Historical run kept for context, not comparable to current results. |
| `deprecated` | Result should not be used for current comparisons. |

## When Scores Become Legacy

Mark prior scores as `legacy_snapshot` when any of these change:

- task manifests are added, removed, or materially edited
- scorer pass/fail logic changes
- v0-candidate metric definitions change
- target app authorization behavior changes
- route aliases, decoys, or seed behavior changes in a way that affects tasks
- baseline adapter behavior changes materially

## Task Additions

New public tasks should include:

- a synthetic-only task manifest
- a vulnerable or secure-control label
- `control_type` for secure controls
- deterministic replay oracle and controls
- task-quality rubric review
- manifest validation
- public validation

Private holdout additions must remain outside public Git history.

## Task Removals

Removing a task should include:

- the reason for removal
- whether prior scores are now legacy
- whether replacement coverage exists for the same app, boundary, and control
  type
- release-note or changelog coverage when a public release exists

Do not silently remove tasks from a scored release line.

## Scorer Changes

Scorer changes should state whether they affect:

- exploit proof
- boundary reasoning
- false-positive control
- safety
- target-request correlation
- invalid-submission handling
- `v0_mean_score`
- legacy `mean_score`

If the change affects pass/fail behavior, re-run current public baselines before
using the changed scorer for public comparison claims.

## Leaderboard Compatibility

Leaderboard rows are comparable only when they use the same:

- benchmark version or release archive
- scored split
- scorer profile
- task set
- leaderboard eligibility policy

Public-split development runs must not be mixed with private-holdout
leaderboard rows as if they are the same evidence class.
