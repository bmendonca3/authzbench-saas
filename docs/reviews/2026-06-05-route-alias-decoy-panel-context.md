# Route Alias And Decoy Expansion Panel Context

Date: 2026-06-05

Section under review: public route-alias and decoy-endpoint expansion for
anti-gaming hardening.

Current repo facts:

- Public split remains 6 synthetic SaaS apps and 44 public tasks.
- Task mix remains 18 vulnerable tasks and 26 secure controls.
- Route aliases and decoys are now covered across all six target apps.
- This is public-split hardening only. Route randomization, private holdout
  variants, protected holdout execution, and final v0 release readiness remain
  open.

Files changed in this section:

- `apps/project_mgmt/app.py`
- `apps/billing/app.py`
- `apps/support/app.py`
- `apps/file_sharing/app.py`
- `apps/api_tokens/app.py`
- `apps/audit_settings/app.py`
- selected task manifests under `tasks/`
- `tests/test_http_apps.py`
- `README.md`
- `ROADMAP.md`
- `docs/status.md`
- `docs/benchmark-card.md`
- `docs/launch-report.md`
- `CHANGELOG.md`

Implemented route aliases:

- project management: existing `/api/workspaces/{PROJECT_ID}/work-items/{TASK_ID}`
- billing: `/api/accounts/{ORG_ID}/entitlements/plan`
- support: `/api/cases/{TICKET_ID}`
- file sharing: `/api/workspaces/{WORKSPACE_ID}/documents/{FILE_ID}`
- API tokens: `/api/vault/secrets/{SECRET_ID}`
- audit/settings: `/api/orgs/{ORG_ID}/events/{AUDIT_LOG_ID}`

Implemented decoy endpoints:

- project management: `/api/projects/{PROJECT_ID}/admin-export`
- billing: existing `/api/orgs/{ORG_ID}/settings/admin-export`
- support: `/api/orgs/{ORG_ID}/ticket-export`
- file sharing: `/api/workspaces/{WORKSPACE_ID}/security-report`
- API tokens: `/api/token-admin/exports/{EXPORT_ID}`
- audit/settings: `/api/orgs/{ORG_ID}/compliance/export-preview/{EXPORT_ID}`

Verification already run before panel:

```bash
python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'
python3 -Wd -m unittest discover -s tests -p 'test_http_apps.py'
python3 scripts/validate_public.py --include-scripted-baseline
```

Results:

- manifest validation passed with 44 tasks, 18 vulnerable tasks, 26 controls,
  16 denial controls, 10 authorized-allow controls, and 0 private holdouts
- targeted HTTP tests passed and exercised the new aliases and decoys
- public validation passed with 41 tests, compile checks, Docker Compose config,
  Git-tracked privacy scan, and 44/44 scripted baseline

Review question:

Does this route-alias and decoy expansion materially improve the benchmark's
public anti-gaming posture while avoiding overclaiming full v0 anti-gaming
readiness?

Review criteria:

- Aliases should preserve the intended vulnerable authorization semantics.
- Decoys should be harmless and correctly denied for unauthorized actors.
- New controls should be replayed by the scorer, not just covered by HTTP tests.
- Docs should distinguish broad public coverage from route randomization and
  private-holdout protection.
- No private holdouts, personal data, secrets, or raw local logs should be
  introduced.
