# v0 Task Build Matrix

This matrix turns the v0 scope target into a concrete build plan. It should be
updated whenever the public or private split changes.

## Current Alpha Split

| App | Public vulnerable | Public controls | Public total |
| --- | ---: | ---: | ---: |
| Project management | 3 | 4 | 7 |
| Billing | 3 | 5 | 8 |
| Support | 3 | 3 | 6 |
| File sharing | 3 | 5 | 8 |
| **Total** | **12** | **17** | **29** |

## v0 Target Split

The v0 public split should land at 40-50 public tasks. The private holdout pack
should land at 20-30 tasks, with 24 preferred for balanced coverage.

| App | Boundary focus | Public target | Private target |
| --- | --- | ---: | ---: |
| Project management | tenant/project/task ownership | 8 | 4 |
| Billing | organization billing roles and settings | 8 | 4 |
| Support | ticket ownership, status writes, invites | 8 | 4 |
| File sharing | workspace files, share links, visibility | 8 | 4 |
| API tokens | token scopes, tenant binding, write limits | 8 | 4 |
| Audit/settings | admin logs, security settings, exports | 6 | 4 |
| **Total** |  | **46** | **24** |

## Required Task Mix

For v0, maintain at least:

- 25 vulnerable tasks across public and private splits
- 25 secure controls across public and private splits
- 10 authorized-allow controls where access should succeed
- 8 private BOLA or tenant/object-boundary holdouts
- 8 private BFLA, invite/membership, token-scope, or role-boundary holdouts
- 8 private secure controls

## Build Order

1. Add API-token public tasks and controls.
2. Add audit/settings public tasks and controls.
3. Add private holdout tasks for the existing four apps.
4. Add private holdout tasks for the remaining new apps.
5. Rerun scripted, live scripted, and model baselines after every scorer or task
   change.

## Holdout Validation

Private manifests must not be committed. Maintainers can validate a local,
ignored holdout pack with:

```bash
python3 scripts/validate_holdout_pack.py
```

The default expects `tasks_private/holdout/**/*.json`, 20-30 private tasks, at
least 12 vulnerable tasks, and at least 8 controls. The preferred v0 holdout
count is 24.
