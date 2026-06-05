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
| API tokens | 3 | 5 | 8 |
| Audit/settings | 3 | 4 | 7 |
| **Total** | **18** | **26** | **44** |

Current public controls are now labeled by subtype:

- 16 denial controls
- 10 authorized-allow controls

## v0 Target Split

The v0 public split should land at 40-50 public tasks. The private holdout pack
should land at 20-30 tasks, with 24 preferred for balanced coverage.

| App | Boundary focus | Public vuln | Public denial | Public allow | Private vuln | Private denial | Private allow | Total |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Project management | tenant/project/task ownership | 4 | 2 | 2 | 2 | 1 | 1 | 12 |
| Billing | organization billing roles and settings | 4 | 2 | 2 | 2 | 1 | 1 | 12 |
| Support | ticket ownership, status writes, invites | 4 | 4 | 1 | 2 | 1 | 1 | 13 |
| File sharing | workspace files, share links, visibility | 4 | 4 | 1 | 2 | 1 | 1 | 13 |
| API tokens | token scopes, tenant binding, write limits | 4 | 4 | 1 | 2 | 1 | 1 | 13 |
| Audit/settings | admin logs, security settings, exports | 3 | 1 | 3 | 2 | 1 | 1 | 12 |
| **Total** |  | **23** | **17** | **10** | **12** | **6** | **6** | **74** |

## Required Task Mix

For v0, maintain at least:

- 25 vulnerable tasks across public and private splits
- at least 40 percent secure controls across public and private splits. For the
  74-task target above, that means at least 30 total secure controls, counting
  denial and authorized-allow controls together
- 10 authorized-allow controls where access should succeed
- 8 private BOLA or tenant/object-boundary holdouts
- 8 private BFLA, invite/membership, token-scope, or role-boundary holdouts
- 8 private secure controls

## Build Order

1. Add private holdout tasks for the six public apps.
2. Expand route aliases and decoys across apps.
3. Add multi-seed private variants for the highest-value public task families.
4. Rerun scripted, live scripted, and model baselines after every scorer or task
   change.

## Holdout Validation

Private manifests must not be committed. Maintainers can validate a local,
ignored holdout pack with:

```bash
python3 scripts/validate_holdout_pack.py
```

The default expects `tasks_private/holdout/**/*.json`, 20-30 private tasks, at
least 12 vulnerable tasks, at least 8 controls, all six app families, no public
task ID or seed reuse, at least 4 denial controls, and at least 4
authorized-allow controls. The preferred v0 holdout count is 24, with 12 private
controls in the target split above.
