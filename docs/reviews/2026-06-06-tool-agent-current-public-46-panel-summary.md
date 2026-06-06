# Current Public Tool-Agent Baseline Panel Summary

Date: 2026-06-06

Scope: `kiro-live-tool-agent-sonnet-current-public-46-summary.json`, its
baseline-registry entry, docs/chart updates, and validation behavior.

## Counted Reviewers

- Gemini 3.5 Flash (High), verified by Antigravity CLI log
- Gemini 3.1 Pro (High), verified by Antigravity CLI log
- Kiro CLI `claude-opus-4.8`, verified against the live Kiro model catalog
- Parent ChatGPT synthesis

Claude Antigravity labels propagated in logs but did not return substantive
review output, so they are not counted. Raw prompts and logs are kept under
ignored `docs/reviews/panel-logs/` and are not part of the public release
artifact.

## Findings And Fixes

Reviewers agreed the current 46-task public tool-agent baseline is a real
baseline increment, not a leaderboard result.

Accepted fixes:

- updated `tests/test_baseline_registry.py` for the new registry state:
  14 baselines, 3 current public model/agent families, 2 repeated families, and
  a present current public tool-agent baseline
- updated README, status, launch, benchmark-card, baseline, and evidence docs so
  they no longer describe the current tool-agent baseline as missing
- added focused charts for model pass rate, exploit-proven success,
  false-positive rate, and boundary reasoning

## Claim Boundary

Supported claim:

`A current 46-task public live HTTP tool-agent baseline exists with per-task
plan artifacts, probe artifacts, and target-request correlation for all tasks.`

Unsupported claims:

- the baseline gate is v0-ready
- the tool-agent row is repeated evidence
- the tool-agent row is private-holdout evidence
- the tool-agent row is leaderboard eligible
- public-split scores are broad model rankings

## Verification

Required before commit:

- `python3 scripts/validate_baseline_registry.py`
- `python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'`
- `python3 scripts/validate_public.py --include-scripted-baseline`
- `python3 scripts/validate_v0_release.py --allow-incomplete`
- privacy checks proving raw results, captures, private holdouts, and raw panel
  logs are untracked
- remote CI after push
