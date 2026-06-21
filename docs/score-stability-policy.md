# Score Stability Policy

AuthZBench-SaaS is released at v0.0, but task and scorer changes are still
expected on the path to v1. This policy keeps old scores understandable when
the benchmark changes.

## Score States

| State | Meaning |
| --- | --- |
| `current_public_split` | Valid for the current public task set and current scorer profile. Model/tool rows must also state whether they are full reruns or `promoted_cohort_delta_merge` composites. |
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

## Promoted-Composite Baselines

When a small private-prep cohort is promoted into `tasks/`, a current model or
tool-agent baseline may be refreshed by merging an immutable prior public split
summary with fresh reruns for exactly the promoted public tasks. Such rows must
use `baseline_construction: promoted_cohort_delta_merge`, set
`not_full_rerun: true`, preserve base and delta summary paths, and recompute the
current public benchmark fingerprint.

Approved wording is "current promoted-composite baseline for the current public
split." Do not call these rows "fresh full reruns" or "fresh 63-task reruns"
unless every task in the public split was actually rerun.

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

The validator encodes those inputs in `comparability_key`. Compare rows directly
only when that key matches. The key includes the benchmark version and commit,
not only task hashes. A runner-emitted `benchmark_fingerprint` is required for
eligibility; post-hoc reconstructed fingerprints are historical evidence, not
proof of the exact task/scoring contract used during execution. Repeated
eligible rows also need one matching source summary per run so variance can be
recomputed. Protected summaries include a deterministic runner-integrity
envelope to detect altered execution metadata; it is not a signature and does
not replace a hosted submission trust boundary. Private-row eligibility also
requires host private-path denial; older workspace-only runs remain historical
evidence.

Public-split development runs must not be mixed with private-holdout
leaderboard rows as if they are the same evidence class.

## See also

- [`docs/scoring-and-submissions.md`](scoring-and-submissions.md) — concrete worked examples of every per-task verdict shape.
