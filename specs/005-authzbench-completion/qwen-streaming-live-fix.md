# Qwen execution packet — repair live packet stream semantics and Ctrl-C

You are the implementation executor. Codex is the DAD/orchestrator and will
independently verify the live behavior.

Working directory:

`/Users/brianmendonca/.codex/bin`

## Exact edit scope

Edit only:

- `/Users/brianmendonca/.codex/bin/qwen-subagent-mcp.py`
- `/Users/brianmendonca/.codex/bin/test-qwen-subagent-mcp.py`

You may set the user-executable bit on `test-qwen-subagent-mcp.py`. Do not edit
the Responses bridge, Codex config, credentials, repository files, or state
artifacts. Do not access secrets.

## Reproduced defects

1. Every completed Codex `agent_message` is emitted as kind `report` with
   message “Qwen produced its final report,” even though more commands and
   messages can follow. A real run showed multiple apparent final reports,
   then later file edits and commands. This is misleading.

2. Pressing Ctrl-C during `--execute-packet` sends SIGINT to the child MCP
   server because `McpClient` launches it in the harness process group. The
   harness then cannot call `qwen_subagent_cancel` and prints
   `execution_cleanup_error=RuntimeError`. The exact Qwen job was eventually
   stopped by server shutdown, but this is not a clean explicit cancel path.

3. `test-qwen-subagent-mcp.py` is not user executable, so direct invocation
   fails with permission denied.

4. `--execute-packet` hardcodes the production Codex binary, making a
   credential-free fake-Codex SIGINT regression difficult.

## Required implementation

1. Correct stream event semantics.
   - A completed `agent_message` before terminal process/turn completion is an
     intermediate assistant message, not a final report.
   - Emit a non-terminal kind such as `assistant_message` with wording that
     explicitly does not claim finality.
   - Preserve the latest bounded assistant text internally for the compatible
     terminal `report` field, but only the terminal job status may be described
     as final/completed.
   - Update deterministic expectations from `report` progress events to the new
     kind.

2. Isolate the child MCP server from terminal SIGINT.
   - Launch `McpClient.process` in its own process session/group.
   - Ensure a `KeyboardInterrupt` in `execute_packet_main` reaches the existing
     `finally` block, calls `qwen_subagent_cancel`, waits for exact process-group
     cleanup, prints `execution_cleanup=cancelled:True`, and then exits as an
     interruption.
   - Do not swallow Ctrl-C as successful completion.
   - Do not use broad process matching or broad kill commands.

3. Make packet execution testable without live credentials.
   - Let `execute_packet_main` use `QWEN_SUBAGENT_CODEX` when set, with the
     current `/Users/brianmendonca/.local/bin/codex` as the default.
   - Preserve production behavior when the variable is unset.

4. Add a deterministic end-to-end SIGINT regression.
   - Launch a nested `--execute-packet` harness with the existing fake Codex
     slow process-tree scenario and a temporary packet/repository/state.
   - Send SIGINT only to the harness process group.
   - Assert the MCP server survived long enough to service explicit cancel,
     stdout contains `execution_cleanup=cancelled:True`, stdout does not contain
     `execution_cleanup_error`, the harness exits nonzero/interrupted, and the
     exact fake parent/descendant process tree is gone.
   - Assert the MCP server process group/session is distinct from the caller.
   - Keep the test bounded and credential-free.

5. Set and verify the user-executable bit on
   `test-qwen-subagent-mcp.py`.

6. Preserve all existing guarantees: ordered persisted progress, exact
   cancellation, timeout cleanup, no secret inheritance, async polling,
   persistence, race coverage, and bridge independence.

## Verification

Run:

```bash
python3 -m py_compile qwen-subagent-mcp.py test-qwen-subagent-mcp.py
python3 test-qwen-subagent-mcp.py
test -x test-qwen-subagent-mcp.py
```

Also run the new SIGINT regression as part of the deterministic suite and
report its explicit pass marker. Do not make a live Alibaba call.

## Completion report

Report exact files changed, mode change, deterministic suite result, SIGINT
cleanup evidence, stream-label change, and residual risk. Implement now; do not
return a plan-only answer.
