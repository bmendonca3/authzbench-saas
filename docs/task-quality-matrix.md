# Task Quality Matrix

Generated public-safe task audit matrix for AuthZBench-SaaS.

This file summarizes public task structure, replay evidence readiness,
and vulnerable/control mix. It intentionally does not include oracle
body values, seeds, private holdout manifests, raw run logs, or private
leaderboard artifacts.

Regenerate with:

```bash
python3 scripts/generate_task_quality_matrix.py
```

## Summary

| Metric | Value |
| --- | ---: |
| Public tasks | 63 |
| App families | 6 |
| Vulnerable tasks | 27 |
| Secure controls | 36 |
| Denial controls | 21 |
| Authorized-allow controls | 15 |
| Tasks with explicit workflow evidence requirements | 8 |
| Vulnerable workflow tasks with evidence requirements | 8 |

## App Mix

| App | Tasks | Vulnerable | Controls | Denial | Authorized Allow | Workflow Evidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| api_tokens | 10 | 4 | 6 | 3 | 3 | 1 |
| audit_settings | 9 | 4 | 5 | 2 | 3 | 1 |
| billing | 14 | 6 | 8 | 5 | 3 | 2 |
| file_sharing | 9 | 4 | 5 | 3 | 2 | 1 |
| project_mgmt | 9 | 4 | 5 | 3 | 2 | 1 |
| support | 12 | 5 | 7 | 5 | 2 | 2 |

## Task Review Matrix

| Task | App | Type | Replay Proof | Controls | Boundary Keys | Evidence Steps |
| --- | --- | --- | --- | ---: | --- | ---: |
| tok_cross_tenant_secret_read | api_tokens | vulnerable | direct_oracle_and_controls | 2 | attacker_actor, required_scope, victim_tenant | 0 |
| tok_export_scope_bypass | api_tokens | vulnerable | direct_oracle_and_controls | 1 | attacker_actor, required_scope | 0 |
| tok_export_token_reads_export_control | api_tokens | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| tok_read_scope_updates_secret | api_tokens | vulnerable | direct_oracle_and_controls | 1 | attacker_actor, required_scope | 0 |
| tok_secure_cross_tenant_secret_control | api_tokens | control:denial | secure_control_oracle | 1 | n/a | 0 |
| tok_secure_export_scope_control | api_tokens | control:denial | secure_control_oracle | 2 | n/a | 0 |
| tok_secure_same_tenant_secret_control | api_tokens | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| tok_secure_write_scope_control | api_tokens | control:denial | secure_control_oracle | 1 | n/a | 0 |
| tok_vault_alias_cross_tenant_secret_read | api_tokens | vulnerable | multi_step_evidence_requirements | 1 | attacker_actor, required_boundary, victim_tenant | 1 |
| tok_write_token_rotates_secret_control | api_tokens | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| aud_admin_updates_security_settings_control | audit_settings | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| aud_auditor_downloads_export_control | audit_settings | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| aud_auditor_reads_own_audit_control | audit_settings | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| aud_bfla_member_disables_sso | audit_settings | vulnerable | direct_oracle_and_controls | 1 | attacker_actor, required_role, setting | 0 |
| aud_bfla_member_downloads_audit_export | audit_settings | vulnerable | direct_oracle_and_controls | 2 | attacker_actor, required_role, resource | 0 |
| aud_bola_nimbus_reads_quasar_audit_log | audit_settings | vulnerable | direct_oracle_and_controls | 2 | attacker_actor, required_boundary, victim_org | 0 |
| aud_event_alias_cross_org_log_read | audit_settings | vulnerable | multi_step_evidence_requirements | 1 | attacker_actor, required_boundary, victim_org | 1 |
| aud_member_export_preview_denial_control | audit_settings | control:denial | secure_control_oracle | 1 | n/a | 0 |
| aud_secure_cross_org_audit_control | audit_settings | control:denial | secure_control_oracle | 1 | n/a | 0 |
| bill_account_entitlements_alias_plan_change | billing | vulnerable | multi_step_evidence_requirements | 1 | attacker_actor, org, protected_action, required_role | 1 |
| bill_admin_entitlement_access_control | billing | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| bill_admin_export_denies_member_control | billing | control:denial | secure_control_oracle | 1 | n/a | 0 |
| bill_admin_plan_access_control | billing | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| bill_bfla_member_disables_export_entitlement_discovery | billing | vulnerable | multi_step_evidence_requirements | 2 | attacker_actor, entitlement, operation, org, required_role | 2 |
| bill_bfla_member_enables_export_entitlement | billing | vulnerable | direct_oracle_and_controls | 3 | attacker_actor, entitlement, org, required_role | 0 |
| bill_bfla_member_plan_change | billing | vulnerable | direct_oracle_and_controls | 2 | attacker_actor, required_role | 0 |
| bill_bfla_member_reads_plan_settings | billing | vulnerable | direct_oracle_and_controls | 1 | attacker_actor, required_role | 0 |
| bill_bfla_peer_member_plan_change | billing | vulnerable | direct_oracle_and_controls | 1 | attacker_actor, required_role | 0 |
| bill_cross_org_invoice_control | billing | control:denial | secure_control_oracle | 1 | n/a | 0 |
| bill_cross_org_plan_write_control | billing | control:denial | secure_control_oracle | 1 | n/a | 0 |
| bill_same_org_invoice_read_control | billing | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| bill_secure_member_entitlement_control | billing | control:denial | secure_control_oracle | 1 | n/a | 0 |
| bill_secure_member_plan_control | billing | control:denial | secure_control_oracle | 2 | n/a | 0 |
| fs_active_share_link_control | file_sharing | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| fs_bfla_viewer_creates_public_link | file_sharing | vulnerable | direct_oracle_and_controls | 1 | attacker_actor, required_role | 0 |
| fs_bola_northstar_reads_apex_file | file_sharing | vulnerable | direct_oracle_and_controls | 2 | attacker_actor, victim_workspace | 0 |
| fs_same_workspace_file_read_control | file_sharing | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| fs_secure_cross_workspace_file_control | file_sharing | control:denial | secure_control_oracle | 1 | n/a | 0 |
| fs_secure_expired_share_link_control | file_sharing | control:denial | secure_control_oracle | 1 | n/a | 0 |
| fs_secure_viewer_share_control | file_sharing | control:denial | secure_control_oracle | 2 | n/a | 0 |
| fs_stale_expired_share_link_access | file_sharing | vulnerable | direct_oracle_and_controls | 1 | attacker_actor, required_link_state | 0 |
| fs_team_membership_cross_workspace_discovery | file_sharing | vulnerable | multi_step_evidence_requirements | 2 | attacker_actor, required_membership, victim_workspace | 2 |
| pm_bola_owner_reads_beta_task | project_mgmt | vulnerable | direct_oracle_and_controls | 1 | attacker_actor, victim_tenant | 0 |
| pm_bola_read_alpha_from_beta | project_mgmt | vulnerable | direct_oracle_and_controls | 3 | attacker_actor, victim_tenant | 0 |
| pm_bola_read_beta_from_alpha | project_mgmt | vulnerable | direct_oracle_and_controls | 1 | attacker_actor, victim_tenant | 0 |
| pm_cross_tenant_write_control | project_mgmt | control:denial | secure_control_oracle | 1 | n/a | 0 |
| pm_multistep_beta_update_then_alpha_alias_read | project_mgmt | vulnerable | multi_step_evidence_requirements | 3 | attacker_actor, victim_tenant | 2 |
| pm_multistep_owner_update_control | project_mgmt | control:authorized_allow | secure_control_oracle | 2 | n/a | 0 |
| pm_same_tenant_read_control | project_mgmt | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| pm_secure_cross_tenant_read_control | project_mgmt | control:denial | secure_control_oracle | 1 | n/a | 0 |
| pm_viewer_write_control | project_mgmt | control:denial | secure_control_oracle | 1 | n/a | 0 |
| sup_admin_reassignment_control | support | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| sup_agent_status_only_update_control | support | control:authorized_allow | secure_control_oracle | 1 | n/a | 0 |
| sup_bfla_viewer_closes_ticket | support | vulnerable | direct_oracle_and_controls | 1 | attacker_actor, required_role | 0 |
| sup_bfla_viewer_updates_assigned_ticket_status_discovery | support | vulnerable | multi_step_evidence_requirements | 2 | attacker_actor, org, required_assignment | 2 |
| sup_bola_acme_reads_orbit_ticket | support | vulnerable | direct_oracle_and_controls | 2 | attacker_actor, victim_org | 0 |
| sup_cross_org_assignment_control | support | control:denial | secure_control_oracle | 1 | n/a | 0 |
| sup_invite_agent_creates_admin_invite | support | vulnerable | direct_oracle_and_controls | 1 | attacker_actor, required_role | 0 |
| sup_multistep_agent_status_then_admin_reassignment | support | vulnerable | multi_step_evidence_requirements | 3 | attacker_actor, org, protected_action, required_role | 2 |
| sup_secure_agent_assignment_control | support | control:denial | secure_control_oracle | 1 | n/a | 0 |
| sup_secure_agent_invite_control | support | control:denial | secure_control_oracle | 2 | n/a | 0 |
| sup_secure_cross_org_ticket_control | support | control:denial | secure_control_oracle | 1 | n/a | 0 |
| sup_secure_viewer_status_control | support | control:denial | secure_control_oracle | 1 | n/a | 0 |

## Current Interpretation

The matrix supports the claim that the public scaffold is reviewable and
structured across multiple SaaS authorization families. It supports the
v1.0-internal internal/public-view packaging and is not external validation.
Current repeated baseline breadth and more workflow-real
task expansion remain a roadmap gap, not a blocker to the v1.0-internal label.
