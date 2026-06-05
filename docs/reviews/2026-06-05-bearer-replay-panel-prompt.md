# Bearer Replay Scorer Review Prompt

Review the AuthZBench-SaaS API-token bearer replay scorer hardening.

Use the context in
`docs/reviews/2026-06-05-bearer-replay-panel-context.md` and inspect the listed
files if needed. Stay read-only. Do not edit files, mutate Git, install
dependencies, upload, browse, or take external actions.

Answer concisely:

1. Whether bearer-token evidence is now first-class scored replay evidence.
2. Whether actor-only replay remains compatible.
3. Whether unknown or mismatched bearer evidence fails closed.
4. What still blocks real v0/live-leaderboard readiness.
