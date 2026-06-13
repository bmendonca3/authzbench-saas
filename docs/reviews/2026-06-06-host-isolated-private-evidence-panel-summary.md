# Host-Isolated Private Evidence Panel Summary

Date: 2026-06-06

## Scope

The panel reviewed two redacted private-holdout summaries and the generated
leaderboard row. It did not receive private manifests or raw per-task results.

## Verified Evidence

- Both runs used benchmark commit
  `fb9e4c792abec779a6ac00150e8b67e964247774` and the same runner-emitted
  benchmark fingerprint.
- Both runs used macOS `sandbox-exec` with host private-path denial enabled.
- The protected-evidence validator accepted two unique host-isolated runs when
  evaluated as no-tools evidence.
- The leaderboard validator accepted one `leaderboard-submission-v1` row as
  eligible with artifact-backed repeat evidence and no warnings.
- Both runs scored `0.5000` on the declared v0 metric. Exploit proof varied
  from 2/12 to 1/12 vulnerable tasks; neither run achieved a full vulnerable
  pass. All 12 controls passed in both runs with no false reports.
- No private manifests, raw results, captures, or panel logs are tracked.

## Panel

Substantive reviews were returned by verified Gemini 3.5 Flash (High), Gemini
3.1 Pro (High), Kiro `claude-opus-4.8`, and the local evidence reviewer.
Claude Sonnet 4.6 (Thinking) and Claude Opus 4.6 (Thinking) labels were
verified, but those runs returned no substantive output and were not counted.

## Decision

The evidence supports one eligible private no-tools baseline row. The public
artifacts are appropriately redacted and resolve the host-isolation blocker for
the holdout and anti-gaming review section.

The evidence does not yet support final v0 release readiness. A fresh
host-isolated private tool-agent run with full target-request correlation,
exact-head validation and CI, and refreshed release evidence are still
required.

## Claims To Avoid

- Do not describe one eligible row as a populated or hosted leaderboard.
- Do not make private-holdout model-ranking claims from one model family.
- Do not claim host-isolated private tool-agent evidence exists yet.
- Do not claim the model solved vulnerable workflows: full vulnerable passes
  were 0/12 in both runs.
