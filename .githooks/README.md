# Optional Git hooks

This repository ships hook scripts under `.githooks/` but does not change your
global Git configuration.

To enable the commit message guard locally:

```sh
git config core.hooksPath .githooks
```

The same rule runs in CI via `scripts/validate_public.py` (history scan) and
`scripts/check_commit_message.py`.
