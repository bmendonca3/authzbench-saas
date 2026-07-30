# AuthZBench-SaaS Agent Instructions

These instructions apply to the entire repository. The workspace-level
`AGENTS.md` remains authoritative for identity, approvals, GitHub safety,
credential handling, preservation, and completion evidence.

## Universal Rules

- Preserve the canonical checkout, all user changes, and all linked worktrees.
- Do not reset, clean, stash, delete, reformat, or weaken tests and validators
  as a recovery tactic.
- Keep local evidence, Kaggle executor evidence, external review, platform
  acceptance, organization approval, hosted operation, and launch claims
  separate.
- Never expose credentials, private holdout bodies, raw private results,
  private routes/seeds, browser profiles, caches, or ignored evidence.
- Do not commit, push, send, upload, publish, authenticate, install
  dependencies, or perform destructive/external actions without current
  authority for that exact effect.
- Direct tests and readback are completion evidence; elapsed effort, model
  output, and adjacent passing checks are not.

## Codex Parent / DAD Mode

Codex owns task shaping, authority decisions, worker scope, canonical edits,
integration, verification, and final claims. It may run repository validators
that inspect maintainer-only aggregate metadata when the current task
authorizes that local validation. It must inspect every worker patch before
integration.

## Qwen/Cline Harness Mode

This mode applies when `QWEN_HARNESS_POLICY` is set or the task packet identifies
Qwen/Cline as the bounded executor.

- You are working in a disposable public-only workspace containing only
  hash-pinned named inputs. The canonical checkout is not your write target.
- Read only the packet and paths admitted by the harness policy. Never read,
  list, search, glob, or probe `tasks_private/`, credentials, ignored results,
  captures, caches, browser state, other worktrees, or paths outside the
  disposable workspace.
- Do not perform repo-wide searches. Use `read_files` for named inputs only.
  `search_codebase` and recursive shell search are unavailable.
- Edit only the exact files listed by the harness. Use the editor tool for
  writes. Do not write through shell commands, Python one-liners, redirection,
  generated rewrites, or temporary scripts.
- No shell commands are admitted. Parent-only verification commands are not
  executor tools.
- Do not use network/browser/MCP tools, credentials, subagents, teams,
  schedules, plugins, package installation, Git mutations, or external
  services.
- After reading the packet and named inputs, make the smallest required edit
  promptly. If the packet is inconsistent or needs another file/command, stop
  and report the exact missing grant instead of investigating broadly.
- Treat a hook denial as a hard boundary. Do not retry the action through a
  different tool or encoding.
- Finish with exact changed files, exact commands/results, claim boundaries,
  and residual uncertainty. Never claim the parent accepted or integrated the
  candidate patch.

The `AGENTS.md` text is guidance. The OS sandbox, generated policy hook,
independent tool ledger, and pre/post workspace audit are the enforcing
controls.
