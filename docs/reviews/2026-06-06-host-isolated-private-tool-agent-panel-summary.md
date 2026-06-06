# Host-Isolated Private Tool-Agent Panel Summary

Date: 2026-06-06

## Scope

The panel reviewed one redacted private tool-agent summary together with the
two host-isolated no-tools summaries and the protected-evidence validator. It
did not receive private manifests, request logs, or raw per-task artifacts.

## Verified Evidence

- The tool-agent run used benchmark commit
  `21e92c793d9f58ee1c50eced5383ce2b16b704d9`.
- Its task and scorer fingerprint matches the two host-isolated no-tools runs.
- The run used macOS `sandbox-exec` with host private-path denial enabled.
- It produced 24/24 model-plan artifacts, 24/24 probe artifacts, 100 executed
  probes, and target-side request correlation for all 24 private tasks.
- The default protected-evidence validator accepted the combined three-run set
  with host isolation and the tool-agent requirement enabled.
- No private manifests, raw results, captures, or panel logs are tracked.

## Panel

Substantive reviews were returned by verified Gemini 3.5 Flash (High), Gemini
3.1 Pro (High), Kiro `claude-opus-4.8`, and the Codex evidence reviewer.
Claude Sonnet 4.6 (Thinking) and Claude Opus 4.6 (Thinking) labels were
verified, but those runs returned no substantive output and were not counted.

## Decision

One host-isolated tool-agent run with 24/24 target correlation satisfies the
documented execution-availability contract. The contract requires one covered
tool-agent summary plus repeated protected evidence overall; it does not make
the single tool-agent run leaderboard eligible or statistically repeatable.

The panel differed only on sequencing. Some reviewers considered the release
field immediately eligible to flip. The stricter disposition is adopted:
commit this redacted source first, then require local validation, privacy
checks, fresh-clone validation, and exact-head CI before changing final
release-readiness metadata.

## Performance Interpretation

The run passed 12/24 tasks, all controls. It submitted seven findings but
proved zero vulnerable tasks and achieved zero full vulnerable passes. Two
planner outputs required safe fallback probes. This is strong execution and
correlation evidence, not strong vulnerable-task performance.

## Claims To Avoid

- Do not call the single tool-agent run repeatable or leaderboard eligible.
- Do not claim the tool-agent proved private-holdout vulnerabilities.
- Do not make private model rankings from asymmetric harness evidence.
- Do not generalize macOS host isolation to every operating system.
- Do not claim final v0 readiness before the source-bearing commit passes all
  final checks.
