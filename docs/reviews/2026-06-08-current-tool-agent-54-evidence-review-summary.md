# Current Tool-Agent 54-Task Evidence Review

Date: 2026-06-08

Reviewer: Kiro `claude-opus-4.6`

Scope:

- `baselines/baseline-registry.json`
- `baselines/kiro-live-tool-agent-sonnet-current-public-54-run1-summary.json`
- `baselines/kiro-live-tool-agent-sonnet-current-public-54-run2-summary.json`
- baseline, v0 release, v1 readiness, and chart tests
- public readiness fixture
- README, goal, status, benchmark-card, claim ledger, baseline credibility,
  baseline variance, v1-prep report, launch report, baseline README, and review
  registry claim text

## Artifact Audit

Verdict: clean.

The artifact audit confirmed:

- registry entry `kiro-live-tool-agent-sonnet-current-public-54` names both run
  artifacts and expects 54 tasks, `kiro_live_tool_agent`,
  `claude-sonnet-4.6`, and `tool-agent`;
- run IDs are distinct:
  `20260608T013814005961Z-9c4b9351` and
  `20260608T014504973620Z-1a19b7fb`;
- both summaries share benchmark commit
  `60322f319a8492aa0feb78f77b9eef5a098f35bd`;
- both summaries share task-set fingerprint
  `f8d19cb89d347d1397f85bf978e6b7b232e8a2f1307fc2ac6ba02674e5c23c9f`;
- both summaries match registry task, model, agent, and harness claims;
- promoted summaries use the relative target log path
  `captures/request-logs-tool-agent-current-54`;
- no real absolute private paths were found in scoped baseline artifacts;
- the only `/Users/example/` strings observed were intentional sensitive-path
  detector test fixtures;
- tests cover run IDs, commit SHA, fingerprint, task count, model, agent,
  harness type, pass count, mean score, exploit-proof metrics, boundary
  reasoning, false positives, invalid submissions, plan/probe artifact counts,
  target-request correlation, planner failures, parser failures, finding totals,
  fallback probes, and target log path.

## Claims Audit

Verdict: clean.

The claims audit confirmed:

- current 54-task public evidence is described as five no-tools families plus
  one repeated live HTTP `claude-sonnet-4.6` tool-agent family;
- 49-task rows are consistently labeled stale for current 54-task comparison;
- the boundary-reasoning calibration study remains scoped to the historical
  49-task public tool-agent pair;
- the current 54-task live tool-agent pair is described as repeating the
  high-exploit-proof, zero-boundary-credit pattern, not as a separate completed
  calibration study;
- docs do not claim `v1-ready`, hosted leaderboard readiness, private ranking
  readiness, or external review completion;
- `docs/goal.md` keeps external review, private holdout, hosted/containerized
  execution, repeated private evidence, task-scale, paper, and final release
  candidate gates open.

## Disposition

No actionable findings.

This review supports the current public 54-task live HTTP tool-agent evidence
promotion only. It is an internal evidence review, not independent external
AppSec, benchmark/evals, or AI-agent/tooling review.
