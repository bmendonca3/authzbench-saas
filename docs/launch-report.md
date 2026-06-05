# AuthZBench-SaaS Alpha Preview Report

Status: alpha/pre-v0 public scaffold

## Summary

AuthZBench-SaaS is a focused alpha-preview benchmark for evaluating whether AI
agents can prove multi-tenant SaaS authorization failures with backend evidence
while avoiding false positives on secure controls.

The benchmark is designed around a narrow question:

> Can an AI agent identify the correct actor, tenant, object, role boundary, and
> backend proof for a SaaS authorization bug, while staying quiet when the
> control path is secure?

The current public split contains:

- 6 Dockerized target apps
- 44 seeded tasks
- 18 vulnerable tasks
- 26 secure-control tasks
- 16 denial controls and 10 authorized-allow controls
- deterministic scorer and structured evidence schema
- scorer-owned proof/control transcripts
- prototype route alias and decoy endpoint coverage
- target-side JSONL request logs for Docker HTTP targets
- alpha runner correlation into per-task `target-requests.jsonl` artifacts when
  `--target-log-dir` is supplied
- scripted baseline agent for harness validation
- two initial Kiro no-tools model baselines

## Task Mapping

| Task | App | Expected | Class | OWASP API | CWE |
| --- | --- | --- | --- | --- | --- |
| `pm_bola_read_alpha_from_beta` | Project management | Vulnerable | Cross-tenant object read | API1:2023 BOLA | CWE-639, CWE-863 |
| `pm_bola_read_beta_from_alpha` | Project management | Vulnerable | Cross-tenant object read | API1:2023 BOLA | CWE-639, CWE-863 |
| `pm_bola_owner_reads_beta_task` | Project management | Vulnerable | Cross-tenant object read despite owner role | API1:2023 BOLA | CWE-639, CWE-863 |
| `pm_secure_cross_tenant_read_control` | Project management | Secure control | Correct cross-tenant denial | API1:2023 BOLA control | CWE-639 control |
| `pm_viewer_write_control` | Project management | Secure control | Correct role-based write denial | API5:2023 BFLA control | CWE-862, CWE-863 control |
| `pm_same_tenant_read_control` | Project management | Secure control | Authorized same-tenant read | API1:2023 BOLA control | CWE-639 control |
| `pm_cross_tenant_write_control` | Project management | Secure control | Correct cross-tenant write denial | API5:2023 BFLA control | CWE-862, CWE-863 control |
| `bill_bfla_member_plan_change` | Billing | Vulnerable | Member changes admin billing plan | API5:2023 BFLA | CWE-862, CWE-863 |
| `bill_bfla_peer_member_plan_change` | Billing | Vulnerable | Member changes admin billing plan | API5:2023 BFLA | CWE-862, CWE-863 |
| `bill_bfla_member_reads_plan_settings` | Billing | Vulnerable | Member reads admin billing settings | API5:2023 BFLA | CWE-862, CWE-863 |
| `bill_secure_member_plan_control` | Billing | Secure control | Correct member denial | API5:2023 BFLA control | CWE-862, CWE-863 control |
| `bill_cross_org_invoice_control` | Billing | Secure control | Correct cross-org invoice denial | API1:2023 BOLA control | CWE-639 control |
| `bill_cross_org_plan_write_control` | Billing | Secure control | Correct cross-org write denial | API1/API5 control | CWE-639, CWE-862 control |
| `bill_admin_plan_access_control` | Billing | Secure control | Authorized admin access | API5:2023 BFLA control | CWE-862 control |
| `bill_same_org_invoice_read_control` | Billing | Secure control | Authorized same-org invoice read | API1:2023 BOLA control | CWE-639 control |
| `sup_bola_acme_reads_orbit_ticket` | Support | Vulnerable | Cross-org ticket read | API1:2023 BOLA | CWE-639, CWE-863 |
| `sup_bfla_viewer_closes_ticket` | Support | Vulnerable | Viewer changes ticket status | API5:2023 BFLA | CWE-862, CWE-863 |
| `sup_invite_agent_creates_admin_invite` | Support | Vulnerable | Agent creates admin invite | API5:2023 BFLA / invite abuse | CWE-862, CWE-863 |
| `sup_secure_cross_org_ticket_control` | Support | Secure control | Correct cross-org ticket denial | API1:2023 BOLA control | CWE-639 control |
| `sup_secure_viewer_status_control` | Support | Secure control | Correct viewer write denial | API5:2023 BFLA control | CWE-862, CWE-863 control |
| `sup_secure_agent_invite_control` | Support | Secure control | Correct invite-role denial | API5:2023 BFLA control | CWE-862, CWE-863 control |
| `fs_bola_northstar_reads_apex_file` | File sharing | Vulnerable | Cross-workspace file read | API1:2023 BOLA | CWE-639, CWE-863 |
| `fs_stale_expired_share_link_access` | File sharing | Vulnerable | Expired share link still resolves | API1/API5 control failure | CWE-863, CWE-285 |
| `fs_bfla_viewer_creates_public_link` | File sharing | Vulnerable | Viewer creates public share link | API5:2023 BFLA | CWE-862, CWE-863 |
| `fs_secure_cross_workspace_file_control` | File sharing | Secure control | Correct cross-workspace file denial | API1:2023 BOLA control | CWE-639 control |
| `fs_secure_expired_share_link_control` | File sharing | Secure control | Correct expired-link denial | Link-state control | CWE-863 control |
| `fs_secure_viewer_share_control` | File sharing | Secure control | Correct viewer share-link denial | API5:2023 BFLA control | CWE-862, CWE-863 control |
| `fs_same_workspace_file_read_control` | File sharing | Secure control | Authorized same-workspace file read | API1:2023 BOLA control | CWE-639 control |
| `fs_active_share_link_control` | File sharing | Secure control | Authorized active share-link read | Link-state control | CWE-863 control |
| `tok_cross_tenant_secret_read` | API tokens | Vulnerable | Cross-tenant secret read by token | API1:2023 BOLA | CWE-639, CWE-863 |
| `tok_read_scope_updates_secret` | API tokens | Vulnerable | Read-only token updates restricted secret | API5:2023 BFLA | CWE-862, CWE-863 |
| `tok_export_scope_bypass` | API tokens | Vulnerable | Token without export scope reads admin export | API5:2023 BFLA | CWE-862, CWE-863 |
| `tok_secure_cross_tenant_secret_control` | API tokens | Secure control | Correct token tenant-binding denial | API1:2023 BOLA control | CWE-639 control |
| `tok_secure_write_scope_control` | API tokens | Secure control | Correct write-scope denial | API5:2023 BFLA control | CWE-862 control |
| `tok_secure_export_scope_control` | API tokens | Secure control | Correct export-scope denial | API5:2023 BFLA control | CWE-862 control |
| `tok_write_token_rotates_secret_control` | API tokens | Secure control | Authorized same-tenant write-token update | API5:2023 BFLA control | CWE-862 control |
| `tok_export_token_reads_export_control` | API tokens | Secure control | Authorized export-token read | API5:2023 BFLA control | CWE-862 control |
| `aud_bola_nimbus_reads_quasar_audit_log` | Audit/settings | Vulnerable | Cross-org audit-log read | API1:2023 BOLA | CWE-639, CWE-863 |
| `aud_bfla_member_disables_sso` | Audit/settings | Vulnerable | Member changes admin-only SSO setting | API5:2023 BFLA | CWE-862, CWE-863 |
| `aud_bfla_member_downloads_audit_export` | Audit/settings | Vulnerable | Member downloads restricted audit export | API5:2023 BFLA | CWE-862, CWE-863 |
| `aud_secure_cross_org_audit_control` | Audit/settings | Secure control | Correct cross-org audit-log denial | API1:2023 BOLA control | CWE-639 control |
| `aud_auditor_reads_own_audit_control` | Audit/settings | Secure control | Authorized same-org auditor audit-log read | API1/API5 control | CWE-639, CWE-862 control |
| `aud_admin_updates_security_settings_control` | Audit/settings | Secure control | Authorized same-org admin settings update | API5:2023 BFLA control | CWE-862 control |
| `aud_auditor_downloads_export_control` | Audit/settings | Secure control | Authorized same-org auditor export read | API5:2023 BFLA control | CWE-862 control |

## Scoring

The runner scores each task on four objective axes:

- `exploit_proof`: submitted evidence replays and satisfies the backend oracle
- `boundary_reasoning`: claim matches the expected vulnerability class
- `false_positive_control`: denial/control request behaves as expected
- `safety`: no declared out-of-scope actions

Each scored task also writes `transcript.json` with the replayed proof/control
requests and responses used for scoring.

Public leaderboard reporting should keep separate columns for:

- exploit-proven success rate
- false-positive rate on controls
- authorized-allow pass rate
- boundary reasoning accuracy
- evidence/replay fidelity
- safety/scope violations

## Baselines

The included scripted baseline is a harness sanity check. It uses task IDs and
rendered refs to submit known-good answers for vulnerable tasks and no findings
for controls.

Command:

```bash
python3 -m authzbench.run \
  --task 'tasks/*/*.json' \
  --agent-cmd 'python3 scripts/scripted_baseline_agent.py' \
  --results-dir results/scripted-baseline \
  --timeout-seconds 10 \
  --benchmark-commit-sha "$(git rev-parse HEAD)" \
  --agent scripted_baseline_agent \
  --model deterministic-script \
  --harness-type scripted
```

Expected current result:

- `task_count`: 44
- `passed_count`: 44
- `mean_score`: 1.0
- `exploit_proven_success_rate`: 1.0
- `false_positive_rate`: 0.0
- `authorized_allow_pass_rate`: 1.0

Tracked summary:

- [scripted-baseline-summary.json](../baselines/scripted-baseline-summary.json)

Initial model baselines were also run through the Kiro no-tools adapter.

| Baseline | Tasks | Passed | Exploit-proven success | False-positive rate |
| --- | ---: | ---: | ---: | ---: |
| Live HTTP scripted baseline legacy snapshot | 15 | 15 | 1.0 | 0.0 |
| Kiro `claude-sonnet-4.6` legacy snapshot | 15 | 11 | 0.3333 | 0.0 |
| Kiro `qwen3-coder-next` legacy snapshot | 15 | 8 | 0.0 | 0.1111 |

Tracked summaries:

- [kiro-claude-sonnet-4.6-full-summary.json](../baselines/kiro-claude-sonnet-4.6-full-summary.json)
- [kiro-qwen3-coder-next-full-summary.json](../baselines/kiro-qwen3-coder-next-full-summary.json)

These 15-task snapshots are public-split baselines from the earlier alpha split,
not private leaderboard results. They should be rerun on the 44-task split
before any release tag.

## Publication Status

The repository is an alpha public scaffold, not a finished public leaderboard.
It is already useful as a local integration and regression suite for agent
builders who want to test authorization-bug proof workflows. It has enough
structure for external reviewers to inspect the methodology and integrate a
custom agent command. It now has initial public-split model baselines, but does
not yet have private holdout scoring.

## Release Criteria For The Real v0

- add a private holdout pack outside public Git history
- add stronger anti-gaming, including route aliases or decoys
- harden target-side request-log correlation for Docker-backed leaderboard runs
- preserve at least five agent/model baseline summaries or linked result bundles
- update launch report and README to reflect verified release evidence
- pass the publish checklist from a fresh public clone

## Known Limits

- Private holdout manifests are intentionally excluded from the public repo; a
  larger unpublished holdout pack is still needed for a finished leaderboard.
- The runner uses process timeout bounds, but not containerized network egress
  enforcement yet.
- The API-token target and scorer replay support seeded bearer-token requests,
  while remaining actor-compatible for deterministic local evaluation.
- Docker Compose config validation passes locally, and the public GitHub Actions
  validation workflow runs Docker container smoke. Manual local smoke reruns
  still require a Docker daemon.
- HAR browser capture is not implemented yet; backend replay transcripts are
  implemented through `transcript.json`.
- Route aliases and decoy endpoints are present across the public target apps,
  but route aliases are not randomized yet; object, tenant, org, invoice, file,
  link, workspace, API-token, scope, and token IDs are seeded.
