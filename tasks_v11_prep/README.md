# v1.1-prep task cohort

This directory holds a parallel cohort of public-style task manifests
that demonstrate the `multi_step_discovery` task type and the plan-4.2
categories the public 60-task split does not cover. The cohort is
named **v1.1-prep** to make it clear that these tasks are part of the
v1.1 wave, not the locked v1.0-internal public split.

## Why a parallel directory

The current public split is locked at 60 tasks. Every public baseline
summary (`baselines/kiro-*-current-public-60-run{1,2}-summary.json`)
is anchored to that 60-task count, and the v1-readiness gate asserts
`public_task_count=60`. Adding tasks under `tasks/` would either:

1. Force a v1.1 rerun of every live public baseline to bring them to
   the new public count, or
2. Make the live baseline summaries stale for the new tasks.

Both are deliberate v1.1 release-time actions. The fix plan section 12
explicitly marks the fresh 60-task public baselines as in-progress
pending the v1.1 wave. This directory is the prep work for that wave.

## Cohort size

The cohort is intentionally small: three tasks, one per category
below. The cohort is validated in isolation by
`tests/test_v11_prep_multistep_discovery.py`.

## Tasks

| Task | App | Plan-4.2 category | Discovery pattern |
| --- | --- | --- | --- |
| `sup_bfla_viewer_updates_assigned_ticket_status_discovery` | support | Team membership boundary; Support agent can view assigned ticket but not unassigned ticket | Viewer reads own assigned ticket to learn `assigned_to: acme_agent`, then attempts to PATCH status through the non-secure route |
| `bill_bfla_member_disables_export_entitlement_discovery` | billing | Billing plan entitlement downgrade | Admin enables the entitlement (authorized baseline), then member disables it through the non-secure entitlement write route |
| `fs_team_membership_cross_workspace_discovery` | file_sharing | Team membership boundary; Cross-org object ID collision | Viewer reads own workspace file through the secure route to learn `workspace_id: northstar`, then attempts to read an Apex file through the bare file API |

## What these tasks do not enter

- The public 60-task count. The v1-readiness gate still asserts
  `public_task_count=60` based on the `tasks/*/*.json` glob.
- The public 60-task live baseline summaries. Those remain anchored
  to the locked 60-task public split.
- The private holdout count. The 48-task private holdout count is
  also anchored to its locked packs.

## What these tasks do enter

- `docs/multi-step-discovery-task-spec.md` (this directory is the
  implementation example for the spec).
- `docs/realism-notes/<app>.md` (the tasks are designed against the
  same app state the realism notes describe).
- The v1.1 release-time plan in the readiness checklist.

## Validation

The cohort validates in isolation:

```
python3 -m pytest tests/test_v11_prep_multistep_discovery.py -v
```

The cohort does not run under the public v1-readiness gate or the
reproduction script. Adding the cohort to either is a v1.1 release
decision and requires regenerating the public 60-task live baselines
and the v1-readiness fixture to the new public count.
