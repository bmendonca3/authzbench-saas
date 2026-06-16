# Realism notes per app

This directory holds a per-app realism note. Each note documents the
real-world authorization pattern the app represents, what is intentionally
simplified, and what an AppSec or SaaS-domain reviewer should look at
before treating a finding here as evidence of a real production gap.

| App | File | Bug-class focus |
| --- | --- | --- |
| billing | [billing.md](billing.md) | BFLA on plan and entitlement writes; alias-route drift |
| api_tokens | [api_tokens.md](api_tokens.md) | Scope-bypass on secret reads, writes, and exports |
| audit_settings | [audit_settings.md](audit_settings.md) | Role-bypass on admin exports; cross-org read via alias |
| file_sharing | [file_sharing.md](file_sharing.md) | Stale or revoked share-link access; viewer-creates-public-link BFLA |
| project_mgmt | [project_mgmt.md](project_mgmt.md) | Cross-tenant BOLA via alias or portfolio routes |
| support | [support.md](support.md) | Agent-reassignment BFLA; agent-creates-admin-invite BFLA |

## How to use this directory

- External AppSec reviewers should read the relevant app file before
  accepting a finding in that domain as evidence of a real production
  gap.
- The fix-plan section 4.4 wish list calls for these notes. The notes
  are hand-curated from each app seed state, route list, and public
  task manifest.
- The notes are descriptive, not normative. They do not modify any
  scoring or boundary decision.

## Source-of-truth pointers

- The app seed states live in `apps/<app>/app.py` under
  `seed_state(seed)`.
- The route list is `public_api_docs()` in the same file.
- The public task list per app is under `tasks/<app>/`.

## How these notes relate to other docs

- `docs/benchmark-spec.md` describes the benchmark scope, thesis, and methodology.
- `docs/benchmark-comparison.md` compares AuthZBench-SaaS to broader
  benchmarks.
- `docs/glossary.md` defines BOLA, BFLA, denial control, and other
  terms used here.
