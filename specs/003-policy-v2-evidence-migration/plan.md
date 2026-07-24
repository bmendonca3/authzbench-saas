# Implementation Plan

1. Inventory current policy-v1 summaries, ignored run bundles, existing v2 scorer
   work, and registry/chart contracts without changing artifacts.
2. Add a versioned re-score schema, digest utilities, migration command, and
   fail-closed validators with adversarial tests.
3. Add policy-isolation checks to registry and chart generation and regenerate
   only outputs whose source contract is traceable.
4. Implement and test an environment-only Gemini Developer API adapter.
5. Run focused and public gates; inspect the complete staged and unstaged diff.
6. Run one Gemini control. If it passes, execute two serial 63-task policy-v2
   rows, preserving raw evidence outside tracked baseline promotion paths.
7. Validate completeness and repeated-run guards; register only eligible rows.

## Stop Conditions

- Stop before hosted execution if migration or public validation fails.
- Stop after one control if authentication, quota, model identity, response
  parsing, or artifact reconciliation fails.
- Stop before promotion if either full row has any infrastructure failure,
  invalid submission, missing artifact, fingerprint mismatch, or policy mixing.
