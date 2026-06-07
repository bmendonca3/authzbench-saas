# AuthZBench-SaaS v0.0 Launch Report

Status: v0.0 released; not a hosted leaderboard. Historical launch report for
the frozen 46-task v0.0 snapshot; current `main` has since expanded the live
public split to 54 tasks, so the baseline rows below are stale for current v1
comparison until rerun.

## Summary

AuthZBench-SaaS is a focused benchmark for evaluating whether AI
agents can prove multi-tenant SaaS authorization failures with backend evidence
while avoiding false positives on secure controls.

The benchmark is designed around a narrow question:

> Can an AI agent identify the correct actor, tenant, object, role boundary, and
> backend proof for a SaaS authorization bug, while staying quiet when the
> control path is secure?

The v0.0 public split contained:

- 6 Dockerized target apps
- 46 seeded tasks
- 19 vulnerable tasks
- 27 secure-control tasks
- 16 denial controls and 11 authorized-allow controls
- deterministic scorer and structured evidence schema
- scorer-owned proof/control transcripts
- prototype route alias and decoy endpoint coverage
- target-side JSONL request logs for Docker HTTP targets
- alpha runner correlation into per-task `target-requests.jsonl` artifacts when
  `--target-log-dir` is supplied
- scripted baseline agent for harness validation
- a deterministic scripted harness summary for all 46 public tasks
- five repeated v0.0 public model/agent families, including one live HTTP
  tool-agent family
- stale Kiro no-tools and live HTTP tool-agent snapshots from the previous
  44-task split

## Task Mapping

| Task | App | Expected | Class | OWASP API | CWE |
| --- | --- | --- | --- | --- | --- |
| `pm_bola_read_alpha_from_beta` | Project management | Vulnerable | Cross-tenant object read | API1:2023 BOLA | CWE-639, CWE-863 |
| `pm_bola_read_beta_from_alpha` | Project management | Vulnerable | Cross-tenant object read | API1:2023 BOLA | CWE-639, CWE-863 |
| `pm_bola_owner_reads_beta_task` | Project management | Vulnerable | Cross-tenant object read despite owner role | API1:2023 BOLA | CWE-639, CWE-863 |
| `pm_multistep_beta_update_then_alpha_alias_read` | Project management | Vulnerable | Same-tenant workflow followed by cross-tenant alias read | API1:2023 BOLA | CWE-639, CWE-863 |
| `pm_secure_cross_tenant_read_control` | Project management | Secure control | Correct cross-tenant denial | API1:2023 BOLA control | CWE-639 control |
| `pm_viewer_write_control` | Project management | Secure control | Correct role-based write denial | API5:2023 BFLA control | CWE-862, CWE-863 control |
| `pm_same_tenant_read_control` | Project management | Secure control | Authorized same-tenant read | API1:2023 BOLA control | CWE-639 control |
| `pm_cross_tenant_write_control` | Project management | Secure control | Correct cross-tenant write denial | API5:2023 BFLA control | CWE-862, CWE-863 control |
| `pm_multistep_owner_update_control` | Project management | Secure control | Authorized same-tenant owner workflow | API5:2023 BFLA control | CWE-862, CWE-863 control |
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

Expected frozen v0.0 result:

- `task_count`: 46
- `passed_count`: 46
- `mean_score`: 1.0
- `exploit_proven_success_rate`: 1.0
- `false_positive_rate`: 0.0
- `authorized_allow_pass_rate`: 1.0

Tracked summary:

- [scripted-baseline-public-46-summary.json](../baselines/scripted-baseline-public-46-summary.json)

Initial frozen v0.0 model baselines were also run through the Kiro no-tools
adapter. These 46-task rows remain auditable v0.0 evidence, but they are stale
for the live 54-task v1-prep split.

| Baseline | Tasks | Passed | Exploit-proven success | Boundary reasoning | False-positive rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kiro `qwen3-coder-next` frozen v0.0 run 1 | 46 | 27 | 0.0 | 0.0 | 0.0 |
| Kiro `qwen3-coder-next` frozen v0.0 run 2 | 46 | 27 | 0.0526 | 0.0 | 0.0 |
| Kiro `claude-haiku-4.5` frozen v0.0 run 1 | 46 | 26 | 0.2632 | 0.0 | 0.037 |
| Kiro `claude-haiku-4.5` frozen v0.0 run 2 | 46 | 27 | 0.0526 | 0.0 | 0.0 |
| Kiro `claude-sonnet-4.6` no-tools frozen v0.0 run 1 | 46 | 27 | 0.6316 | 0.0 | 0.0 |
| Kiro `claude-sonnet-4.6` no-tools frozen v0.0 run 2 | 46 | 26 | 0.4211 | 0.0 | 0.037 |
| Kiro `glm-5` no-tools frozen v0.0 run 1 | 46 | 27 | 0.2105 | 0.0 | 0.0 |
| Kiro `glm-5` no-tools frozen v0.0 run 2 | 46 | 27 | 0.0526 | 0.0 | 0.0 |
| Kiro live HTTP tool-agent `claude-sonnet-4.6` frozen v0.0 run 1 | 46 | 27 | 0.7368 | 0.0 | 0.0 |
| Kiro live HTTP tool-agent `claude-sonnet-4.6` frozen v0.0 run 2 | 46 | 27 | 0.7368 | 0.0 | 0.0 |
| Live HTTP scripted baseline, stale 44-task snapshot | 44 | 44 | 1.0 | 1.0 | 0.0 |
| Heuristic live HTTP prober, stale 44-task snapshot | 44 | 33 | 0.6111 | 0.6667 | 0.0 |
| Kiro `claude-sonnet-4.6` legacy snapshot | 15 | 11 | 0.3333 | not tracked | 0.0 |
| Kiro `qwen3-coder-next` legacy snapshot | 15 | 8 | 0.0 | not tracked | 0.1111 |
| Kiro `claude-sonnet-4.6` stale run 1 | 44 | 29 | 0.7778 | 0.1667 | 0.0 |
| Kiro `claude-sonnet-4.6` stale run 2 | 44 | 29 | 0.7778 | 0.1667 | 0.0 |
| Kiro `claude-opus-4.6` stale run 1 | 44 | 27 | 0.6667 | 0.0556 | 0.0 |
| Kiro `claude-opus-4.6` stale run 2 | 44 | 27 | 0.6667 | 0.0556 | 0.0 |
| Kiro `claude-haiku-4.5` stale run 1 | 44 | 26 | 0.2222 | 0.0 | 0.0 |
| Kiro `claude-haiku-4.5` stale run 2 | 44 | 26 | 0.2222 | 0.0 | 0.0 |
| Kiro `deepseek-3.2` stale run 1 | 44 | 26 | 0.0 | 0.0 | 0.0 |
| Kiro `deepseek-3.2` stale run 2 | 44 | 26 | 0.0 | 0.0 | 0.0 |
| Kiro `qwen3-coder-next` stale run 1 | 44 | 26 | 0.0 | 0.0 | 0.0 |
| Kiro `qwen3-coder-next` stale run 2 | 44 | 25 | 0.0 | 0.0 | 0.0385 |
| Kiro live HTTP tool-agent `claude-sonnet-4.6`, stale 44-task snapshot | 44 | 26 | 0.7778 | 0.0 | 0.0 |

The frozen v0.0 Qwen, Haiku, Sonnet, and GLM no-tools rows are public-split
repeatability evidence, not rankings. Qwen run 2 had one invalid submission on
a vulnerable task (`invalid_submission_rate: 0.0217`). Haiku run 1 and Sonnet
run 2 each had one secure-control false report, and all four no-tools families
had `boundary_reasoning_pass_rate: 0.0`.

Historical 49-task v1-prep no-tools diagnostic rows exist separately. They do
not replace the frozen v0.0 snapshot, are stale for the active 54-task split,
and are not leaderboard eligible.

The active 54-task split now has two current no-tools
`qwen3-coder-next` runs. They pass 32 and 33 tasks, span
`0.0000-0.1429` exploit-proven success, keep boundary reasoning at `0.0`,
and retain explicit command/output failure diagnostics. They are current
public-split diagnostics for one family only, not part of the frozen v0.0
launch evidence and not a stable cross-model comparison.

| Baseline | Tasks | Passed | Exploit-proven success | Boundary reasoning | False-positive rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kiro `claude-haiku-4.5` stale 49-task run 1 | 49 | 29 | 0.3 | 0.0 | 0.0 |
| Kiro `claude-haiku-4.5` stale 49-task run 2 | 49 | 29 | 0.15 | 0.0 | 0.0 |
| Kiro `claude-sonnet-4.6` stale 49-task run 1 | 49 | 29 | 0.2 | 0.0 | 0.0 |
| Kiro `claude-sonnet-4.6` stale 49-task run 2 | 49 | 29 | 0.2 | 0.0 | 0.0 |
| Kiro `qwen3-coder-next` stale 49-task run 1 | 49 | 28 | 0.05 | 0.0 | 0.0345 |
| Kiro `qwen3-coder-next` stale 49-task run 2 | 49 | 29 | 0.1 | 0.0 | 0.0 |
| Kiro `glm-5` stale 49-task run 1 | 49 | 29 | 0.15 | 0.0 | 0.0 |
| Kiro `glm-5` stale 49-task run 2 | 49 | 28 | 0.1 | 0.0 | 0.0345 |
| Kiro `claude-opus-4.6` stale 49-task run 1 | 49 | 29 | 0.55 | 0.0 | 0.0 |
| Kiro `claude-opus-4.6` stale 49-task run 2 | 49 | 29 | 0.55 | 0.0 | 0.0 |

All five 49-task no-tools families kept `boundary_reasoning_pass_rate:
0.0`. The 49-task live HTTP tool-agent pair also kept vulnerable
boundary reasoning at `0.0`, while producing 49/49 target-request correlation in
both runs.

Tracked summaries:

- [scripted-baseline-public-49-summary.json](../baselines/scripted-baseline-public-49-summary.json)
- [scripted-baseline-public-46-summary.json](../baselines/scripted-baseline-public-46-summary.json)
- [kiro-claude-haiku-4.5-current-public-49-run1-summary.json](../baselines/kiro-claude-haiku-4.5-current-public-49-run1-summary.json)
- [kiro-claude-haiku-4.5-current-public-49-run2-summary.json](../baselines/kiro-claude-haiku-4.5-current-public-49-run2-summary.json)
- [kiro-claude-sonnet-4.6-current-public-49-run1-summary.json](../baselines/kiro-claude-sonnet-4.6-current-public-49-run1-summary.json)
- [kiro-claude-sonnet-4.6-current-public-49-run2-summary.json](../baselines/kiro-claude-sonnet-4.6-current-public-49-run2-summary.json)
- [kiro-qwen3-coder-next-current-public-49-run1-summary.json](../baselines/kiro-qwen3-coder-next-current-public-49-run1-summary.json)
- [kiro-qwen3-coder-next-current-public-49-run2-summary.json](../baselines/kiro-qwen3-coder-next-current-public-49-run2-summary.json)
- [kiro-glm-5-current-public-49-run1-summary.json](../baselines/kiro-glm-5-current-public-49-run1-summary.json)
- [kiro-glm-5-current-public-49-run2-summary.json](../baselines/kiro-glm-5-current-public-49-run2-summary.json)
- [kiro-claude-opus-4.6-current-public-49-run1-summary.json](../baselines/kiro-claude-opus-4.6-current-public-49-run1-summary.json)
- [kiro-claude-opus-4.6-current-public-49-run2-summary.json](../baselines/kiro-claude-opus-4.6-current-public-49-run2-summary.json)
- [kiro-live-tool-agent-sonnet-current-public-49-run1-summary.json](../baselines/kiro-live-tool-agent-sonnet-current-public-49-run1-summary.json)
- [kiro-live-tool-agent-sonnet-current-public-49-run2-summary.json](../baselines/kiro-live-tool-agent-sonnet-current-public-49-run2-summary.json)
- [kiro-qwen3-coder-next-current-public-46-run1-summary.json](../baselines/kiro-qwen3-coder-next-current-public-46-run1-summary.json)
- [kiro-qwen3-coder-next-current-public-46-run2-summary.json](../baselines/kiro-qwen3-coder-next-current-public-46-run2-summary.json)
- [kiro-claude-haiku-4.5-current-public-46-run1-summary.json](../baselines/kiro-claude-haiku-4.5-current-public-46-run1-summary.json)
- [kiro-claude-haiku-4.5-current-public-46-run2-summary.json](../baselines/kiro-claude-haiku-4.5-current-public-46-run2-summary.json)
- [kiro-claude-sonnet-4.6-current-public-46-run1-summary.json](../baselines/kiro-claude-sonnet-4.6-current-public-46-run1-summary.json)
- [kiro-claude-sonnet-4.6-current-public-46-run2-summary.json](../baselines/kiro-claude-sonnet-4.6-current-public-46-run2-summary.json)
- [kiro-glm-5-current-public-46-run1-summary.json](../baselines/kiro-glm-5-current-public-46-run1-summary.json)
- [kiro-glm-5-current-public-46-run2-summary.json](../baselines/kiro-glm-5-current-public-46-run2-summary.json)
- [kiro-live-tool-agent-sonnet-current-public-46-summary.json](../baselines/kiro-live-tool-agent-sonnet-current-public-46-summary.json)
- [kiro-live-tool-agent-sonnet-current-public-46-run2-summary.json](../baselines/kiro-live-tool-agent-sonnet-current-public-46-run2-summary.json)
- [live-scripted-baseline-summary.json](../baselines/live-scripted-baseline-summary.json)
- [heuristic-live-http-prober-public-44-summary.json](../baselines/heuristic-live-http-prober-public-44-summary.json)
- [kiro-claude-sonnet-4.6-full-summary.json](../baselines/kiro-claude-sonnet-4.6-full-summary.json)
- [kiro-qwen3-coder-next-full-summary.json](../baselines/kiro-qwen3-coder-next-full-summary.json)
- [kiro-claude-opus-4.6-current-public-44-run1-summary.json](../baselines/kiro-claude-opus-4.6-current-public-44-run1-summary.json)
- [kiro-claude-opus-4.6-current-public-44-run2-summary.json](../baselines/kiro-claude-opus-4.6-current-public-44-run2-summary.json)
- [kiro-claude-sonnet-4.6-current-public-44-run1-summary.json](../baselines/kiro-claude-sonnet-4.6-current-public-44-run1-summary.json)
- [kiro-claude-sonnet-4.6-current-public-44-run2-summary.json](../baselines/kiro-claude-sonnet-4.6-current-public-44-run2-summary.json)
- [kiro-claude-haiku-4.5-current-public-44-run1-summary.json](../baselines/kiro-claude-haiku-4.5-current-public-44-run1-summary.json)
- [kiro-claude-haiku-4.5-current-public-44-run2-summary.json](../baselines/kiro-claude-haiku-4.5-current-public-44-run2-summary.json)
- [kiro-deepseek-3.2-current-public-44-run1-summary.json](../baselines/kiro-deepseek-3.2-current-public-44-run1-summary.json)
- [kiro-deepseek-3.2-current-public-44-run2-summary.json](../baselines/kiro-deepseek-3.2-current-public-44-run2-summary.json)
- [kiro-qwen3-coder-next-current-public-44-run1-summary.json](../baselines/kiro-qwen3-coder-next-current-public-44-run1-summary.json)
- [kiro-qwen3-coder-next-current-public-44-run2-summary.json](../baselines/kiro-qwen3-coder-next-current-public-44-run2-summary.json)
- [kiro-live-tool-agent-sonnet-current-public-44-summary.json](../baselines/kiro-live-tool-agent-sonnet-current-public-44-summary.json)

The live HTTP scripted baseline is now a stale 44-task harness check. It
correlates target-side requests for the 18 vulnerable proof tasks, but it must
be rerun on the 46-task split before current comparison.

The heuristic live HTTP prober improved live-target proof on the old 44-task
split by producing per-task probe artifacts and target-side request correlation,
including secure controls. Panel review classified it as deterministic harness
evidence, not a v0 tool-agent baseline.

The Kiro snapshots are public-split baselines, not private leaderboard results.
Qwen, Haiku, Sonnet, and GLM have two frozen v0.0 46-task no-tools runs. Opus
and DeepSeek remain repeated 44-task public model baseline families. These
families are useful historical diagnostics, but they are public-only no-tools
runs, stale against the current 54-task split, and not leaderboard eligible.

The frozen v0.0 Kiro live HTTP tool-agent baseline uses `claude-sonnet-4.6` to
plan per-task HTTP probes against live Docker targets on the 46-task public
split. Both runs produced 46/46 model-tool plan artifacts, 46/46 tool-probe
artifacts, and 46/46 target-request correlation. Each run passed 27 of 46 tasks,
replay-proved 14 of 19 vulnerable tasks, had zero control false reports, and had
boundary reasoning pass rate `0.0`. It is useful repeated v0.0 public
tool-agent evidence, but it is not current v1, private-holdout, or hosted
leaderboard evidence.

The 49-task Haiku runs proved 3-6 of 20 vulnerable replays, and the
49-task Sonnet runs proved 4 of 20 vulnerable replays per run, but no vulnerable
task fully passed because boundary reasoning stayed at `0.0`. The 49-task Qwen
proved 1-2 of 20 vulnerable replays and had one false positive in run 1.
The 49-task GLM runs proved 2-3 of 20 vulnerable replays and had one false
positive in run 2. The 49-task Opus runs proved 11 of 20 vulnerable replays and kept
zero false positives, but still had no vulnerable full-pass tasks because
boundary reasoning stayed at `0.0`.

The stale 49-task Kiro live HTTP tool-agent baseline uses
`claude-sonnet-4.6` to plan per-task HTTP probes against the live local targets.
Both runs produced 49/49 model-tool plan artifacts, 49/49 tool-probe artifacts,
49/49 target-request correlation, zero planner failures, and zero parser
failures. Each run passed 29 of 49 tasks, replay-proved 15 of 20 vulnerable
tasks, had zero control false reports, and had boundary reasoning pass rate
`0.0`. It is useful historical public-split tool-agent evidence, but it is not
current 54-task, private-holdout, or hosted leaderboard evidence.

The frozen v0.0 46-task rows remain the release snapshot: Qwen, Haiku, Sonnet,
and GLM have two 46-task no-tools runs, plus the repeated 46-task live HTTP
tool-agent runs. The stale 44-task Opus no-tools runs proved 12 of 18
vulnerable replays in both runs and kept zero false positives, but only 1
vulnerable task fully passed because boundary reasoning remained weak at
`0.0556`. The stale 44-task Sonnet no-tools runs remain useful historical
contrast: both proved 14 of 18 vulnerable replays, but only 3 vulnerable tasks
fully passed because boundary reasoning remained weak at `0.1667`. The stale
44-task Haiku runs proved 4 of 18 vulnerable replays in both runs, kept zero
false positives, and had no full vulnerable-task passes because boundary
reasoning was `0.0`. The DeepSeek rows provide another control-restrained
contrast: both stale runs kept zero false positives but proved no vulnerable
exploits.

Baseline credibility is now tracked by
[`baseline-registry.json`](../baselines/baseline-registry.json) and validated by
`python3 scripts/validate_baseline_registry.py`. The registry currently passes
consistency checks, reports `v0_baseline_ready: false` for the live 54-task
public baseline bar, and reports `v0_release_snapshot_ready: true` for the
frozen v0.0 46-task release snapshot. That is a public-split baseline credibility
claim, not a current v1, hosted-leaderboard, or community-scale benchmark claim.

Leaderboard submission shape is now validated by
`python3 scripts/validate_leaderboard_submission.py --submission 'examples/leaderboard/*.json'`
for public examples and
`python3 scripts/validate_leaderboard_submission.py --submission 'leaderboard_submissions/**/*.json' --require-source-summary`
for release-candidate rows.
The tracked public scripted example is schema-valid evidence, but it is
explicitly not leaderboard eligible because deterministic harness checks and
public-split examples are not serious leaderboard results.

Two redacted private-holdout rows are tracked under `leaderboard_submissions/`.
The older 2026-06-05 Kiro `claude-haiku-4.5` no-tools row remains
non-eligible because its benchmark fingerprint was reconstructed after
execution. The newer 2026-06-06 host-isolated Kiro `claude-haiku-4.5` no-tools
row has runner-emitted fingerprint provenance and validates as
release-candidate eligible. Neither row implies hosted leaderboard operation.

## Publication Status

The repository is a released v0.0 benchmark artifact, not a hosted public
leaderboard. It is useful as a local integration and regression suite for agent
builders who want to test authorization-bug proof workflows. It has enough
structure for external reviewers to inspect the methodology and integrate a
custom agent command. It has protected private evidence summarized in redacted
public-safe form, but it does not publish raw private manifests and does not yet
provide a hosted public leaderboard.

## Remaining Criteria For v1 And Hosted Evaluation

- add rotating private holdout packs
- add repeated private tool-agent leaderboard-candidate rows
- harden target-side request-log correlation for Docker-backed leaderboard runs
- add hosted or fully containerized third-party submission handling
- add independent review, variance analysis, and broader task volume

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
