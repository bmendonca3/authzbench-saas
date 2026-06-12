# AuthZBench-SaaS Harbor Task

Read the rendered context JSON for actors, targets, API docs, and output schema:

- `environment/context.json`

Write the agent submission to:

- `/logs/artifacts/submission.json`

This is a secure-control task. Return an AuthZBench-SaaS submission with `findings: []` unless you have explicit evidence that the control failed.

The verifier runs the AuthZBench-SaaS scorer. Do not rely on prose-only claims.
