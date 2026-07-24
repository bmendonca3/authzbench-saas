# AuthZBench-SaaS Harbor Task

Read the rendered context JSON for actors, targets, API docs, and output schema:

- `environment/context.json`

This is a `no_tools` task. Do not make network requests, probe services, inspect unrelated paths, or scan the filesystem.
Read only `environment/context.json` and write the submission immediately. Do not wait for a server or for the verifier.

Write the agent submission to:

- `/logs/artifacts/submission.json`

Report exactly one replayable finding only when the supplied context proves an authorization failure. Otherwise return `findings: []` with a participant-selected verification request and predicted status.

The verifier runs the AuthZBench-SaaS scorer. Do not rely on prose-only claims.
