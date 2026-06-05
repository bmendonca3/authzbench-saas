# Kiro Live Tool-Agent Baseline Panel Summary

Section: baseline methodology and live-agent evidence.

Disposition: accepted for the alpha/pre-v0 public-split baseline checkpoint.

The panel accepted this slice as a real current public tool-agent baseline, not
another deterministic harness check. The adapter asks Kiro `claude-sonnet-4.6`
to plan HTTP probes from task context, executes those probes against live Docker
targets, and only submits a finding when live probe evidence supports it.

## Verified Reviewers

- Gemini 3.5 Flash (High): accepted. Verified propagated label in panel log.
- Gemini 3.1 Pro (High): accepted. Verified propagated label in panel log.
- Claude Sonnet 4.6 (Thinking): label verified, but the run produced an empty
  review output, so it is not counted for substantive findings.
- Claude Opus 4.6 (Thinking): label verified, but the run produced an empty
  review output, so it is not counted for substantive findings.
- ChatGPT reviewer: parent-review fallback only because no subagent slot was
  available.

Raw panel logs are intentionally untracked under `docs/reviews/panel-logs/`.

## Accepted Evidence

- Adapter and tests:
  - `scripts/kiro_live_tool_agent.py`
  - `tests/test_kiro_live_tool_agent.py`
- Public-safe baseline summary:
  - `baselines/kiro-live-tool-agent-sonnet-current-public-44-summary.json`
- Registry and validator:
  - `baselines/baseline-registry.json`
  - `scripts/validate_baseline_registry.py`
- Public-claim docs:
  - `README.md`
  - `baselines/README.md`
  - `docs/baseline-credibility.md`
  - `docs/status.md`
  - `docs/launch-report.md`
  - `docs/benchmark-card.md`

The committed-SHA run reported:

- 44 public tasks
- 44/44 target-request correlation
- 44/44 model-tool plan artifacts
- 44/44 tool-probe artifacts
- 100 executed live HTTP probes
- 0 planner parse errors
- 0 planner failures
- 0 control false reports

## Findings And Disposition

1. Medium: summary veracity depends on local run evidence.
   Disposition: accepted with residual risk. The public repo intentionally does
   not commit raw Kiro stdout/stderr, request logs, transcripts, or result
   bundles. The tracked summary is acceptable for a public baseline registry,
   but final leaderboard evidence still needs artifact-backed submission
   validation and protected execution.

2. Low: `docs/reviews/review-registry.json` still said a true tool-agent
   baseline was missing.
   Disposition: fixed. The registry now links this summary and says a true
   public-split tool-agent baseline exists while keeping the section not
   v0-ready.

3. Low: docs could conflate `v0_baseline_ready` with full `v0_ready`.
   Disposition: fixed. Public docs now say the baseline sub-gate is ready, but
   strict v0 remains blocked by leaderboard submissions, release evidence,
   final review, and protected leaderboard execution.

## Residual v0 Blockers

- Release-candidate leaderboard submissions are still missing.
- The strict review registry is not fully v0-ready.
- `docs/release-evidence.json` still has no true release-evidence fields.
- Protected/isolated leaderboard execution remains required.
- Public-split results are still not private-holdout leaderboard results.

## Local Checks

```bash
python3 -Wd -m unittest discover -s tests -p 'test_kiro_live_tool_agent.py'
python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_v0_release.py --allow-incomplete
```
