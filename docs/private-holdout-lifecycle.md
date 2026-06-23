> [!NOTE]
> **Consolidation Notice**: This file is slated for consolidation. Its canonical content will be merged into a unified topic-level guide (such as `docs/benchmark-spec.md` or `docs/scoring-and-submissions.md`) in subsequent consolidation phases.

# Private Holdout Lifecycle Policy

This document is the public-safe lifecycle policy for the private
holdout packs that back the v1.0-internal release. It is the source
of truth for how a pack is created, validated, activated, rotated,
and retired; for who can inspect private manifests; and for what the
public repo is allowed to publish about a pack at each lifecycle
stage.

## Pack lifecycle stages

| Stage | When a pack is in this stage | Public artifact shape |
| --- | --- | --- |
| `preparation` | Tasks are being drafted and quality-reviewed; not yet routed through the public scorer. | No public summary. |
| `shadow` | The pack is wired into the runner on a private host, but the public scorer is not yet pointed at it. Public row eligibility requires the active pack's fingerprint. | `private-holdout-shadow-public-summary.json` (count + fingerprint only). |
| `active` | The pack is the source of truth for v1-internal scoring. Public row eligibility requires this pack's fingerprint. | `private-holdout-active-public-summary.json` (count + fingerprint only). |
| `retired` | The pack is no longer scored against. Held for legacy audit and external review reproducibility only. | Public summary records retired status; no per-task body, route, or seed. |

## Pack creation

1. Draft tasks under `tasks_private/holdout/drafts/` with the same
   schema as the public tasks under `tasks/`. The drafts must
   include `expected_vulnerable`, `oracle`, `expected_boundary`,
   `controls`, and (for multistep tasks) `evidence_requirements`.
2. Run the task through
   `python3 scripts/generate_task_oracle_audit.py --check`. The
   schema gate must pass.
3. Add the draft to a candidate pack directory under
   `tasks_private/holdout/<pack-id>/`. Each pack directory carries
   its own `manifest.json` with the pack-level fingerprint, version,
   created_at, task_count, vulnerable_count, control_count, and the
   list of task paths.

## Inspection access

| Role | Can see | Cannot see |
| --- | --- | --- |
| Maintainer (rotates packs) | All private manifests, seeds, raw transcripts, redacted summaries | n/a |
| AppSec external reviewer (v2) | Active and shadow packs in a controlled environment (see `docs/private-review-protocol.md`) | Raw task files outside the controlled environment |
| Public | Active/shadow/retired pack summary, count, fingerprint, role | Per-task private contents |

## Fingerprint rules

- `fingerprint_sha256` is computed by
  `authzbench.core.benchmark_fingerprint` over the canonical sorted
  list of `(path, manifest)` pairs.
- When a task is added, removed, or modified, the pack's fingerprint
  changes. A new public summary artifact must be published under the
  same pack id with the new fingerprint before any leaderboard row
  references the new fingerprint.
- The fingerprint is the key that ties a leaderboard row to a pack.
  Rows that carry a different fingerprint are not comparable.

## Rotation cadence

- The active pack is rotated on a documented cadence or on any of the
  retirement triggers below. The default rotation cadence is every
  `retire_after_submissions` submissions (default 25).
- Rotation moves the current active pack to `retired`, promotes the
  current shadow pack to `active`, and prepares a new `shadow` pack.
- Rows scored against the retired pack are kept as `legacy_snapshot`
  rows; they are not merged with active-pack rows.

## Retirement triggers

A pack is retired immediately when any of the following occur:

- Private task leakage is suspected or confirmed.
- The scorer or oracle has a defect that affects pack validity.
- A major public task or score-policy change makes in-flight rows
  incomparable.
- External review identifies a material task-quality issue.
- The active pack has aged past the documented rotation cadence.

## Leakage handling

If a private task body, route, seed, oracle string, raw output, or
credential is exposed publicly:

1. The active pack is retired immediately and the leaked task is
   removed from the active pack.
2. A new active pack is promoted from the shadow pack; if the shadow
   pack is also affected, a fresh shadow pack is prepared from
   drafts.
3. A redacted incident note is added to the public summary
   explaining what was leaked, what was rotated, and what rows are
   affected.
4. The leaked task is moved to the `retired` pack directory and
   flagged `retire_reason: leakage`.

## Public summary rules

Public artifacts may publish:

- Active / shadow / retired pack id, role, version, created_at,
  activated_at, retired_at, fingerprint_sha256, task_count,
  vulnerable_count, control_count.
- A redacted incident note on leakage events.

Public artifacts may **never** publish:

- Per-task private manifest bodies, including private task bodies.
- Per-task private routes, seeds, oracle strings, or expected
  boundaries.
- Raw per-request transcripts of private runs.
- Real-SaaS credentials, tokens, or private customer data.
- Local absolute paths from the maintainer host.

The CI privacy scan at `scripts/validate_public.py` enforces the
forbidden-pattern allow-list before any public artifact is published.

## Reviewer-safe validation commands

Reviewers can verify the public-safe boundary without accessing private
manifests:

```bash
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/check_claim_boundary.py
```

`validate_public.py` runs the public task suite, baseline registry,
task quality gate, claim-boundary check, and the public-view readiness
fixture match. `check_claim_boundary.py` verifies that no forbidden
claim phrases appear outside allowed negation contexts. Neither command
requires access to `tasks_private/` or any private pack.

See [`docs/validation-commands.md`](validation-commands.md) for the full
validator reference and [`docs/claims-and-evidence.md`](claims-and-evidence.md)
for the canonical claim ledger.

## See also

- [`docs/benchmark-spec.md`](benchmark-spec.md#5-holdout-and-contamination-prevention):
  the contamination model that explains why the public split and
  private holdouts are kept disjoint.
- [`docs/holdout-rotation-protocol.md`](holdout-rotation-protocol.md):
  the rotation procedure.
- [`docs/private-review-protocol.md`](private-review-protocol.md):
  how external AppSec reviewers can audit the active and shadow
  packs under controlled conditions.
- [`artifact/private-holdout-rotation-metadata.template.json`](../artifact/private-holdout-rotation-metadata.template.json):
  the schema for new pack entries.
