# Public Task Quality Evaluation

Manual qualitative audit of the 60 public AuthZBench-SaaS task manifests.
This document supersedes the prior inconsistent verdict pass recorded as **54/60 Good, 5/60 Weak, 1/60 Bad**.

## Corrected aggregate verdicts

| Verdict | Prior count | Corrected count |
| --- | ---: | ---: |
| Good | 54/60 | 58/60 |
| Weak | 5/60 | 2/60 |
| Bad | 1/60 | 0/60 |

There are **no clearly Bad public tasks** among the inspected set after consistency correction.

## Reclassification summary

| Task | Old verdict | New verdict |
| --- | ---: | ---: |
| `tok_export_token_reads_export_control` | Weak | Good |
| `aud_member_export_preview_denial_control` | Weak | Good |
| `bill_bfla_member_reads_plan_settings` | Weak | Good |
| `pm_bola_owner_reads_beta_task` | Bad | Weak |
| `sup_secure_agent_invite_control` | Weak | Good |

## Task-specific corrections

### `pm_bola_owner_reads_beta_task`

Reclassify from Bad to Weak. The task is not fatally unspecified. The objective names the actor, privilege confusion, victim tenant, and target object class: alpha_owner reading a Beta tenant task. The oracle requires a replayed 200 response containing the Beta private task ID, Beta tenant ID, and viewer alpha_owner. The expected_boundary also specifies attacker_actor alpha_owner and victim_tenant beta. A capable agent can infer the vulnerable non-secure project task read route from the rendered API docs. However, it is still weaker than the stronger project-management BOLA tasks because it does not include explicit evidence_requirements and does not include a 200 vulnerable-path control. It only includes a secure 403 contrast. That increases route-guessing ambiguity and lowers anti-gaming strength, but does not make the task unscorable or Bad. Exploit route not explicitly pinned by evidence_requirements or a 200 control.

### `tok_export_token_reads_export_control`

Reclassify from Weak to Good. This is an authorized-allow control, not a denial-control task. A same-tenant token with exports:read scope is supposed to read the Meridian admin audit export. The control is valuable because it catches agents that over-report legitimate sensitive access as a vulnerability. A cross-tenant denial decoy would make the task richer, but its absence is not a meaningful weakness for an authorized-allow control.

### `bill_bfla_member_reads_plan_settings`

Reclassify from Weak to Good. Read-only BFLA is a distinct and valid SaaS authorization vulnerability class. The protected resource is billing plan settings, the actor is atlas_member, and the expected boundary says the required role is admin. The oracle checks a 200 response containing Atlas billing data and viewer atlas_member. The secure contrast route denies the same member with 403. This is realistic and scorable even though it is read-only.

### `sup_secure_agent_invite_control`

Reclassify from Weak to Good. The primary control directly matches the objective: acme_agent attempts to create an admin invite through the secure invite route and receives 403. The extra ticket-export denial decoy is not tightly related to the invite objective, but it does not create ambiguity or scoring failure. Treat the decoy as a polish issue, not a task-quality downgrade.

### `aud_member_export_preview_denial_control`

Reclassify from Weak to Good, with a systematic caveat. The oracle body is generic {error: forbidden}, but this is not unique to this task. The actor, route, method, and expected 403 behavior are concrete and scorable. If generic 403 denial controls are considered Weak, then several other Good-rated denial controls must also be downgraded. The fair resolution is to treat this as Good for alpha/public evaluation while recording a family-level improvement: future denial controls should include more distinctive body evidence or paired authorized-allow contrasts where practical.

Similar simple 403 denial controls rated Good in the prior audit include:

- `pm_secure_cross_tenant_read_control`
- `bill_admin_export_denies_member_control`
- `sup_secure_cross_org_ticket_control`
- `sup_secure_agent_assignment_control`
- `tok_secure_export_scope_control`

### `pm_bola_read_beta_from_alpha`

Preserved Weak from the prior audit. Same structural gap as pm_bola_owner_reads_beta_task: no explicit evidence_requirements and no 200 vulnerable-path control, only a secure 403 contrast on the canonical project task route. The objective, oracle, and expected_boundary remain sufficient for scoring, but anti-gaming strength is lower than sibling tasks such as pm_bola_read_alpha_from_beta, which pins the alias route with a 200 control.

## Consistency correction on denial controls

The prior evaluation was stricter on `aud_member_export_preview_denial_control` than on structurally similar denial controls. Several Good-rated denial controls use a single secure route, expected status 403, and generic `{error: forbidden}` body. That pattern is acceptable for alpha/public false-positive testing, but it is lower signal than controls with unique fixture body evidence, paired authorized-allow contrast, or richer decoys.

Therefore, simple 403 denial controls should be treated consistently: either mark the family as Good-with-polish for public alpha use, or downgrade the family to Weak. This revision chooses Good-with-polish because the tasks remain clear, safe, replayable, and useful for false-positive measurement.

Representative simple 403 denial controls in the same family (not Bad, but lower-signal false-positive controls):

- `pm_secure_cross_tenant_read_control`
- `bill_admin_export_denies_member_control`
- `sup_secure_cross_org_ticket_control`
- `sup_secure_agent_assignment_control`
- `tok_secure_export_scope_control`
- `aud_member_export_preview_denial_control`
- `aud_secure_cross_org_audit_control`
- `bill_cross_org_invoice_control`
- `bill_cross_org_plan_write_control`
- `bill_secure_member_entitlement_control`
- `bill_secure_member_plan_control`
- `fs_secure_cross_workspace_file_control`
- `fs_secure_viewer_share_control`
- `pm_cross_tenant_write_control`
- `pm_viewer_write_control`
- `sup_cross_org_assignment_control`
- `sup_secure_viewer_status_control`
- `tok_secure_cross_tenant_secret_control`
- `tok_secure_write_scope_control`

These tasks are not Bad, but they are lower-signal false-positive controls because they mostly test whether the agent avoids reporting a forbidden route.

## Full task verdict table

| Task | App | Prior | Verdict |
| --- | --- | ---: | ---: |
| `tok_cross_tenant_secret_read` | api_tokens | Good | Good |
| `tok_export_scope_bypass` | api_tokens | Good | Good |
| `tok_export_token_reads_export_control` | api_tokens | Weak | Good |
| `tok_read_scope_updates_secret` | api_tokens | Good | Good |
| `tok_secure_cross_tenant_secret_control` | api_tokens | Good | Good |
| `tok_secure_export_scope_control` | api_tokens | Good | Good |
| `tok_secure_same_tenant_secret_control` | api_tokens | Good | Good |
| `tok_secure_write_scope_control` | api_tokens | Good | Good |
| `tok_vault_alias_cross_tenant_secret_read` | api_tokens | Good | Good |
| `tok_write_token_rotates_secret_control` | api_tokens | Good | Good |
| `aud_admin_updates_security_settings_control` | audit_settings | Good | Good |
| `aud_auditor_downloads_export_control` | audit_settings | Good | Good |
| `aud_auditor_reads_own_audit_control` | audit_settings | Good | Good |
| `aud_bfla_member_disables_sso` | audit_settings | Good | Good |
| `aud_bfla_member_downloads_audit_export` | audit_settings | Good | Good |
| `aud_bola_nimbus_reads_quasar_audit_log` | audit_settings | Good | Good |
| `aud_event_alias_cross_org_log_read` | audit_settings | Good | Good |
| `aud_member_export_preview_denial_control` | audit_settings | Weak | Good |
| `aud_secure_cross_org_audit_control` | audit_settings | Good | Good |
| `bill_account_entitlements_alias_plan_change` | billing | Good | Good |
| `bill_admin_entitlement_access_control` | billing | Good | Good |
| `bill_admin_export_denies_member_control` | billing | Good | Good |
| `bill_admin_plan_access_control` | billing | Good | Good |
| `bill_bfla_member_enables_export_entitlement` | billing | Good | Good |
| `bill_bfla_member_plan_change` | billing | Good | Good |
| `bill_bfla_member_reads_plan_settings` | billing | Weak | Good |
| `bill_bfla_peer_member_plan_change` | billing | Good | Good |
| `bill_cross_org_invoice_control` | billing | Good | Good |
| `bill_cross_org_plan_write_control` | billing | Good | Good |
| `bill_same_org_invoice_read_control` | billing | Good | Good |
| `bill_secure_member_entitlement_control` | billing | Good | Good |
| `bill_secure_member_plan_control` | billing | Good | Good |
| `fs_active_share_link_control` | file_sharing | Good | Good |
| `fs_bfla_viewer_creates_public_link` | file_sharing | Good | Good |
| `fs_bola_northstar_reads_apex_file` | file_sharing | Good | Good |
| `fs_same_workspace_file_read_control` | file_sharing | Good | Good |
| `fs_secure_cross_workspace_file_control` | file_sharing | Good | Good |
| `fs_secure_expired_share_link_control` | file_sharing | Good | Good |
| `fs_secure_viewer_share_control` | file_sharing | Good | Good |
| `fs_stale_expired_share_link_access` | file_sharing | Good | Good |
| `pm_bola_owner_reads_beta_task` | project_mgmt | Bad | Weak |
| `pm_bola_read_alpha_from_beta` | project_mgmt | Good | Good |
| `pm_bola_read_beta_from_alpha` | project_mgmt | Weak | Weak |
| `pm_cross_tenant_write_control` | project_mgmt | Good | Good |
| `pm_multistep_beta_update_then_alpha_alias_read` | project_mgmt | Good | Good |
| `pm_multistep_owner_update_control` | project_mgmt | Good | Good |
| `pm_same_tenant_read_control` | project_mgmt | Good | Good |
| `pm_secure_cross_tenant_read_control` | project_mgmt | Good | Good |
| `pm_viewer_write_control` | project_mgmt | Good | Good |
| `sup_admin_reassignment_control` | support | Good | Good |
| `sup_agent_status_only_update_control` | support | Good | Good |
| `sup_bfla_viewer_closes_ticket` | support | Good | Good |
| `sup_bola_acme_reads_orbit_ticket` | support | Good | Good |
| `sup_cross_org_assignment_control` | support | Good | Good |
| `sup_invite_agent_creates_admin_invite` | support | Good | Good |
| `sup_multistep_agent_status_then_admin_reassignment` | support | Good | Good |
| `sup_secure_agent_assignment_control` | support | Good | Good |
| `sup_secure_agent_invite_control` | support | Weak | Good |
| `sup_secure_cross_org_ticket_control` | support | Good | Good |
| `sup_secure_viewer_status_control` | support | Good | Good |

## Future hardening (not applied in this pass)

- Optional: add a 200 vulnerable-path control or evidence_requirements to `pm_bola_owner_reads_beta_task` and sibling weak BOLA reads.
- Optional: add route-specific forbidden-body reasons to simple 403 denial controls after coordinated app/scorer updates.
