# Qwen/Cline Executor Harness

The harness runs exact model `qwen3.8-max-preview` with Cline `3.0.47` and
`xhigh` reasoning. Codex remains the parent/DAD: it chooses scope, reviews the
candidate, runs verification, and decides whether to integrate. Qwen never
writes the canonical checkout.

## What is enforced

Each task contract pins the source commit and SHA-256 of every public input.
The harness byte-copies only those files into a disposable workspace; it does
not copy `.git`, `.agents`, `tasks_private/`, ignored results, credentials,
caches, or unrelated repository files. New writable files are precreated with
a deterministic one-line marker so Cline's editor can replace them exactly
without needing directory-wide create permission or its unreliable empty-file
insertion path.

Four controls are independent:

1. `AGENTS.md` and a generated `.cline/rules/00-qwen-harness-contract.md`
   explain the exact task and allowlists to Qwen.
2. `.cline/hooks/PreToolUse.py` cancels and audits any unlisted tool, read, or
   write. Cline hooks are defense-in-depth because Cline 3.0.47 fails open when
   a hook crashes.
3. macOS `sandbox-exec` allows file content only from declared system runtime
   paths, isolated Cline state, harness controls, and the disposable workspace;
   it permits writes only to exact candidate files and isolated state, and
   permits outbound network only to the local Qwen bridge on port `8790`.
   Metadata traversal remains available for macOS runtime resolution. The
   harness refuses to run if direct filesystem and network self-tests do not
   prove the content/write/network bounds.
4. A full pre/post manifest rejects extra files, deletions, mode changes,
   unlisted edits, missing required edits, hook/stream disagreement, malformed
   events, a wrong/missing terminal result, or any model other than
   `qwen3.8-max-preview`.

The compact stream groups reasoning deltas into coherent thoughts while the raw
NDJSON retains every token event. A repetition breaker stops the run after
three failed calls by the same tool against the same path set.

Raw stdout, stderr, a compact live stream, hook audit, manifests, and the final
summary share one evidence directory under
`~/.local/state/qwen-cline-harness/`. Only an accepted run gets
`candidate.patch` and copied candidate files.

## Create and run a task

The packet and every readable/writable existing file must be named. `init`
computes their current hashes; `--create` predeclares a new marker file.
Deterministic outputs should also use `--expect-output-sha PATH=SHA256`; the
candidate is rejected unless the final bytes match.

```bash
python3 scripts/run_qwen_cline_harness.py init \
  --task-id bounded-doc-fix \
  --task "Apply the packet's exact documentation correction." \
  --packet specs/006-qwen-cline-harness/example-packet.md \
  --read docs/status.md \
  --write docs/status.md \
  --require-change docs/status.md \
  --output /tmp/bounded-doc-fix.json

python3 scripts/run_qwen_cline_harness.py preflight \
  --contract /tmp/bounded-doc-fix.json

python3 scripts/run_qwen_cline_harness.py run \
  --contract /tmp/bounded-doc-fix.json
```

`timeout_seconds: 0` means no provider wall-clock timeout. The runtime pin keeps
the model, maximum reasoning level, bridge, Cline version, and compiled-binary
hash fixed. A Cline upgrade requires an explicit pin review.

## Parent acceptance

An accepted harness result is still only a candidate. Codex must read the raw
tool ledger and patch, confirm the declared source hashes still match, inspect
every changed line, apply the change deliberately, and run the recorded
verification commands with argv arrays and `shell=False`. The harness never
commits, pushes, sends, uploads, publishes, installs dependencies, or performs
external actions.

One rejected remediation run is the maximum recommended retry. If the same
boundary or execution failure repeats, switch executor instead of weakening
the harness.
