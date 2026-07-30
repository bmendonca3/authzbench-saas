# Qwen cancellation smoke packet

This is a no-write cancellation smoke test.

- Do not edit, create, delete, or chmod any file.
- Do not run network requests.
- Do not inspect credentials or private data.
- Read the current working directory path and wait for the parent to cancel.
- If not canceled, return exactly `QWEN_CANCEL_SMOKE_UNEXPECTED_COMPLETION`.
