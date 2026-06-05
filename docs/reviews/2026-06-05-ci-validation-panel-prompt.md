# CI Validation Panel Prompt

Review the CI validation change in AuthZBench-SaaS.

Use the context packet and inspect the changed files if available. Do not edit
files. Return concise findings only:

1. Does the workflow run the right public validation gate?
2. Are permissions and triggers appropriate for a public benchmark repo?
3. Does the local test meaningfully guard the workflow?
4. Do docs avoid claiming remote CI has passed before it is checked?
5. What should the parent verify or fix before committing?
