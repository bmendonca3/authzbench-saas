# AuthZBench-SaaS Harbor Task

Read the rendered context JSON for actors, targets, API docs, and output schema:

- `environment/context.json`

This is a `no_tools` analysis task, not a software-debugging task. Perform exactly these actions:
1. Read `environment/context.json`.
2. Write the required JSON to `/logs/artifacts/submission.json` using the supplied output schema. When the context does not prove a failure, use `findings: []` and include the requested verification prediction.
3. Finish immediately by issuing `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` as a standalone command.
Do not run `find`, scan the filesystem, inspect packages or logs, make network or localhost requests, modify other files, or wait for a server or verifier.

Write the agent submission to:

- `/logs/artifacts/submission.json`

Report exactly one replayable finding only when the supplied context proves an authorization failure. Otherwise return `findings: []` with a participant-selected verification request and predicted status.

The verifier runs the AuthZBench-SaaS scorer. Do not rely on prose-only claims.
