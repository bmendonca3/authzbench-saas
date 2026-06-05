Review the AuthZBench-SaaS Docker runtime CI change.

Use the context file `docs/reviews/2026-06-05-docker-runtime-ci-panel-context.md`
and inspect the current uncommitted diff if available.

Return only:

1. Top findings with severity.
2. Evidence paths or command references.
3. What must be verified locally or remotely before this can be treated as a
   real release gate.

Focus on correctness, CI/runtime reliability, cleanup behavior, release-doc
honesty, privacy/public-repo safety, and whether this meaningfully reduces the
v0 blocker list. Do not edit files, install dependencies, mutate git, or browse
the web.
