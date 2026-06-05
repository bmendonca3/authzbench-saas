# Final Task-Mix Panel Context

Date: 2026-06-05

Question for reviewers: can the `task_realism_vulnerability_control_mix`
section be marked v0-ready for the current alpha/pre-v0 release-candidate
evidence, without claiming the whole benchmark is v0-ready?

## Public Positioning

The public repo must continue to say alpha/pre-v0 until
`scripts/validate_v0_release.py --allow-incomplete` reports `v0_ready: true`.

This review is only about the task realism and vulnerable/control mix section.
It does not decide holdout anti-gaming readiness, multi-seed private scoring, or
final release readiness.

## Public Split Evidence

The public split contains 44 tasks across 6 synthetic SaaS apps.

Per-app public task counts:

| App | Total | Vulnerable | Controls | Denial Controls | Authorized-Allow Controls |
| --- | ---: | ---: | ---: | ---: | ---: |
| api_tokens | 8 | 3 | 5 | 3 | 2 |
| audit_settings | 7 | 3 | 4 | 1 | 3 |
| billing | 8 | 3 | 5 | 3 | 2 |
| file_sharing | 8 | 3 | 5 | 3 | 2 |
| project_mgmt | 7 | 3 | 4 | 3 | 1 |
| support | 6 | 3 | 3 | 3 | 0 |

Public aggregate:

- 44 public tasks
- 18 vulnerable tasks
- 26 secure-control tasks
- 16 denial controls
- 10 authorized-allow controls
- 6 apps

The public split stays within the v0 target of 40-50 public tasks and at least
6 apps.

## Private Holdout Aggregate Evidence

The ignored private holdout pack is not tracked in Git. The current
`scripts/validate_holdout_pack.py` output reports:

```json
{
  "manifest_count": 24,
  "private_holdout_count": 24,
  "vulnerable_count": 12,
  "control_count": 12,
  "denial_control_count": 6,
  "authorized_allow_control_count": 6,
  "app_counts": {
    "api_tokens": 4,
    "audit_settings": 4,
    "billing": 4,
    "file_sharing": 4,
    "project_mgmt": 4,
    "support": 4
  },
  "route_variant_count": 24,
  "decoy_variant_count": 24,
  "rehearsal_manifest_count": 0,
  "public_structure_overlap_count": 0,
  "leaderboard_suitable": true,
  "passed": true
}
```

This context intentionally omits private task IDs, seeds, routes, oracle bodies,
filesystem paths, and raw manifests.

## Combined V0 Task-Mix Evidence

The current local strict validator reports the `task_mix` gate as passed:

```json
{
  "total_tasks": 68,
  "total_vulnerable_tasks": 30,
  "total_controls": 38,
  "authorized_allow_control_count": 16,
  "control_ratio": 0.5588
}
```

This satisfies the explicit v0 task-mix thresholds:

- at least 25 vulnerable tasks
- at least 30 secure-control tasks
- at least 10 authorized-allow controls
- at least 40% controls
- 20-30 protected private holdout tasks

## Existing Section Reviews

The following public expansion sections already have tracked summaries:

- `2026-06-05-support-expansion-panel-summary.md`
- `2026-06-05-file-sharing-panel-summary.md`
- `2026-06-05-api-tokens-panel-summary.md`
- `2026-06-05-audit-settings-panel-summary.md`

Current registry note for this section:

> Public app/task expansion has sectional review and the ignored private holdout
> pack now satisfies the local task-mix gate, but this section still needs a
> final task-mix review before it can be marked v0-ready.

## Known Non-Task-Mix Blockers

These should not block the task-mix section unless the reviewer believes they
directly undermine task realism or mix:

- `holdout_contamination_anti_gaming` remains not v0-ready.
- Multi-seed private scoring is not complete.
- Route-alias/decoy anti-gaming review is not final.
- Final privacy/package/release-readiness review is not complete.
- The overall strict validator still reports `v0_ready: false`.

## Requested Reviewer Output

Return:

1. Whether `task_realism_vulnerability_control_mix` can be marked v0-ready.
2. Any accepted blockers that should prevent marking this section ready.
3. Any wording constraints needed to avoid overclaiming.
4. The exact evidence you relied on.
