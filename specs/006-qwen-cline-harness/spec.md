# Qwen/Cline Executor Harness Specification

Status: active
Evidence date: 2026-07-29
Classification: full Spec Kit workflow (`specify` CLI unavailable; artifacts
maintained manually)

## Outcome

Provide a reusable, observable, fail-closed way to use Qwen 3.8 Max Preview as
a bounded AuthZBench-SaaS implementation worker without granting it direct
access to maintainer-private paths or automatic writes to the canonical
checkout.

Codex remains the parent/DAD. Qwen produces a candidate patch in a disposable
public-only clone. The parent accepts, rejects, or manually integrates that
patch after reviewing tool events, filesystem scope, tests, and claims.

## User Stories

### US-1 — Safe bounded implementation

As the parent orchestrator, I can declare the packet, hash-pinned readable
public files, exact writable files, predeclared new files, optional exact
output hashes, and parent-only validation commands. Qwen can edit only within
that contract, and the harness rejects every other tool, path, and mutation.

Acceptance:

- a permitted file read and edit can run;
- a `tasks_private/` read is cancelled before the tool executes;
- an absolute path outside the disposable workspace is cancelled;
- an unlisted command or tool is cancelled;
- an unlisted write or deletion makes the final candidate fail closed.

### US-2 — Observable execution

As the parent orchestrator, I can watch compact reasoning, tool, usage, final,
and exact-model events while preserving the complete raw NDJSON and hook audit.

Acceptance:

- raw stdout, stderr, hook decisions, summary, and candidate patch are retained
  under one evidence directory;
- non-JSON Cline warnings do not break event parsing;
- the final summary records model, iterations, usage, exit status, scope
  violations, and changed paths.

### US-3 — Efficient executor behavior

As the parent orchestrator, I can give Qwen concise workspace instructions that
favor bounded action over repeated discovery while preserving honest blockers.

Acceptance:

- repository `AGENTS.md` distinguishes universal rules from Qwen harness mode;
- Qwen is told to use only named inputs, make the smallest edit promptly, and
  stop rather than broaden scope;
- the pinned runtime and every accepted terminal record use `xhigh` thinking.

### US-4 — Parent-owned integration

As the parent orchestrator, I receive a candidate patch but the canonical
checkout is never modified automatically.

Acceptance:

- the harness operates in a byte-materialized disposable workspace with no
  `.git` directory;
- the canonical worktree hash/status is unchanged by a harness run;
- a patch is emitted only when Cline succeeds, no hook denial occurs, and the
  pre/post snapshot contains no out-of-scope change.

## Functional Requirements

- **FR-001 — Workspace instructions:** Add a repository-root `AGENTS.md` that
  Cline loads automatically and that preserves existing workspace authority.
- **FR-002 — Declarative contract:** Validate a versioned JSON contract with a
  frozen source commit, packet, SHA-256-bound public inputs, predeclared new
  files, exact write/required-change sets, optional exact output hashes,
  parent-only verification argv, model, thinking level, retry limit, and
  optional timeout.
- **FR-003 — Private-path absence:** Byte-copy only explicitly named regular
  public inputs. Never materialize `.git`, `.agents`, `tasks_private/`, ignored
  evidence, credentials, caches, or unrelated repository files.
- **FR-004 — Pre-tool enforcement:** A workspace `PreToolUse` hook must cancel
  unknown tools, denied paths, out-of-workspace paths, and unlisted
  reads/writes, while recording call IDs in a separate audit. The hook is
  defense-in-depth because Cline 3.0.47 hooks fail open on runtime failure.
- **FR-005 — Symlink containment:** Reject path resolution that escapes the
  disposable workspace and fail setup on outward-pointing workspace symlinks.
- **FR-006 — Post-run enforcement:** Hash the workspace before and after the
  run and reject new, changed, deleted, or mode-changed paths outside the exact
  write allowlist.
- **FR-007 — No automatic integration:** Retain a candidate patch and changed
  file copies in evidence storage; never apply them to the source checkout.
- **FR-008 — Stream durability:** Preserve raw NDJSON/stderr while emitting a
  compact warning-tolerant event stream that groups token deltas into coherent
  reasoning/text updates.
- **FR-009 — Fail-closed result:** Any hook denial, malformed terminal result,
  hook/stream ledger mismatch, wrong provider/model, nonzero Cline exit,
  missing expected write, output-hash mismatch, repetition stop, or scope
  mismatch makes the run rejected.
- **FR-010 — No external authority:** The harness must not commit, push, send,
  publish, use project credentials, or authorize external effects.
- **FR-011 — OS containment:** Refuse to run unless the macOS sandbox directly
  proves declared workspace reads, outside-content/write denial, loopback
  bridge access, and denial of a second live loopback port. File contents are
  allowlisted; writes are exact-file or isolated-state only.
- **FR-012 — Runtime provenance:** Pin Cline version/binary hash, provider,
  model, thinking level, bridge, task contract, controls, policy, rule, and
  sandbox profile; retain their hashes in the run summary.
- **FR-013 — Repetition breaker:** Stop after three failed calls by the same
  tool against the same path set rather than allowing an equivalent loop.

## Success Criteria

- **SC-001:** Deterministic hook tests prove allow and deny behavior for all
  supported tools and sensitive path classes.
- **SC-002:** Harness tests prove allowed patch export and rejection of
  out-of-scope writes/deletes without changing the canonical source.
- **SC-003:** A live Qwen run reports exact provider/model
  `openai-compatible/qwen3.8-max-preview`, creates only its admitted sandbox
  artifact, satisfies its exact output hash, and produces an accepted evidence
  bundle.
- **SC-004:** An adversarial hook smoke cancels a private-path request before
  execution and records the denial.
- **SC-005:** Focused tests, claim/privacy checks, workflow checks, whitespace,
  and the strongest feasible public gate pass.

## Non-Goals

- The deprecated macOS `sandbox-exec` boundary is practical local containment,
  not a claim of protection against a malicious kernel exploit or an
  unreviewed replacement native binary.
- It does not make Qwen the default executor or let Qwen integrate its own
  patch.
- It does not authorize private holdout access, credentials, network tools,
  hosted runs, commits, pushes, review sends, uploads, or publication.
- `AGENTS.md` and model reasoning are defense-in-depth, not enforcement by
  themselves.

## Adversarial Completion Checks

- Try a repo-wide search tool, a direct `tasks_private/` read, `../` traversal,
  an absolute source-checkout path, a symlink/hardlink escape, a shell tool, an
  unlisted tool, an out-of-scope edit, an allowed-file delete/mode change, a
  wrong output hash, malformed/duplicate terminal events, and three repeated
  same-path tool failures.
- Confirm that a passing live smoke did not merely avoid the forbidden action;
  separately invoke the hook with the hostile payload and observe `cancel`.
- Confirm the evidence patch is produced from the disposable baseline, not from
  stale `HEAD` or the canonical dirty worktree.
