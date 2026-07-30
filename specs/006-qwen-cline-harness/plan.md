# Qwen/Cline Executor Harness Plan

## Technical Approach

1. Add repository `AGENTS.md` with universal preservation rules and a distinct
   Qwen harness mode.
2. Add `.cline/hooks/PreToolUse.py` as fast, audited defense-in-depth. It reads
   a generated policy, validates every tool call, records the call ID, and
   emits `{"cancel": true}` on a violation.
3. Add `scripts/run_qwen_cline_harness.py`.
   - validate the task contract;
   - byte-copy only hash-pinned named public regular files;
   - exclude all ambient repository/user configuration;
   - reject symlinks, hardlinks, devices, traversal, and case/Unicode
     collisions;
   - snapshot all non-Git workspace files;
   - pin and self-test an OS sandbox with exact content/write/network bounds;
   - invoke the isolated Cline profile against
     `openai-compatible/qwen3.8-max-preview` at `xhigh`;
   - preserve raw and compact streams;
   - compare hook and stream ledgers plus the post-run snapshot;
   - enforce optional exact output hashes and a repetition breaker;
   - export a patch only for accepted exact-write paths;
   - never mutate the canonical checkout.
4. Add deterministic tests with a fake Cline executable and direct hook
   payloads before any live provider smoke.
5. Run one admitted, exact-hash live sandbox edit and one direct hostile hook
   payload.

## File Boundary

- `AGENTS.md`
- `.cline/hooks/PreToolUse.py`
- `scripts/run_qwen_cline_harness.py`
- `tests/test_qwen_cline_harness.py`
- `docs/qwen-cline-harness.md`
- `specs/006-qwen-cline-harness/`
- ignored durable `GOAL_STATE.md`

No benchmark tasks, apps, scorer logic, private evidence, model baselines, or
external review dispositions change.

## Constitution And Safety Gates

- Preserve the dirty canonical worktree and linked worktrees.
- Never copy `tasks_private/`, credentials, ignored raw evidence, browser
  profiles, or caches into the disposable workspace.
- Qwen receives no shell/search/web/skills/MCP/subagent/team tool authority.
  Recorded verification argv remain parent-only.
- Exact write paths are required; directory write grants and wildcards are
  rejected.
- Parent integration remains manual.
- Provider traffic is the existing loopback bridge only. A live second
  loopback listener and all non-loopback destinations are denied by the OS
  profile.

## Verification

Fast loop:

```bash
python3 -m pytest -q tests/test_qwen_cline_harness.py
python3 -m py_compile scripts/run_qwen_cline_harness.py .cline/hooks/PreToolUse.py
git diff --check
```

Adversarial loop:

```bash
python3 tests/test_qwen_cline_harness.py
python3 scripts/run_qwen_cline_harness.py --contract <smoke-contract> --dry-run
```

Final:

```bash
python3 scripts/check_claim_boundary.py
python3 scripts/check_markdown_links.py
codex-workflow-check --strict
python3 scripts/validate_public.py --include-scripted-baseline
```

## Rollback

Remove the five implementation/documentation files and the feature packet. The
existing Cline installation, model bridge, canonical repository data, and
AuthZBench benchmark behavior are otherwise unchanged.
