# Sonnet Current Public 46 Panel Summary

Date: 2026-06-06

Scope: repeated current-public no-tools Kiro `claude-sonnet-4.6` baseline
summaries, baseline registry update, generated chart data, and public claim
wording in commit `2b411254078598a64bbfe2c623e2327eed8d1cff`.

## Counted Reviewers

- Gemini 3.5 Flash (High), verified by the panel runner CLI log
- Gemini 3.1 Pro (High), verified by the panel runner CLI log
- panel reviewer

Claude Sonnet 4.6 and Claude Opus 4.6 panel runner labels were verified by logs
but did not return substantive review text. Kiro CLI `claude-opus-4.8` was
attempted from the live model catalog, but the reviewer failed under
non-interactive tool restrictions and is not counted.

Raw prompts and logs are kept under ignored `docs/reviews/panel-logs/` and are
not part of the public release artifact.

## Consensus

Reviewers agreed that the Sonnet no-tools checkpoint improves benchmark
credibility because it adds a fourth repeated current public model/agent family
without weakening the gate. The two summaries have:

- 46 public tasks each
- distinct run IDs and run artifacts
- matching public task fingerprint, score policy, and evidence contract
- `harness_type: no-tools-model`
- `agent: kiro_baseline_agent`
- `model: claude-sonnet-4.6`

Reviewers also agreed that the result is useful precisely because it is not a
simple leaderboard-looking win. Across the two public runs, Sonnet proved more
vulnerable replays than Qwen or Haiku, but vulnerable boundary reasoning stayed
at `0.0`, so no vulnerable task fully passed. Run 2 also produced one
secure-control false report.

## Claim Boundary

Supported claim:

`AuthZBench-SaaS now has four repeated current-public model/agent-family
baselines on the 46-task public split, including three no-tools Kiro model
families and one live HTTP tool-agent family. The baseline gate still requires
one more repeated current family before v0 readiness.`

Unsupported claims:

- v0 or v1 readiness
- private-holdout Sonnet performance
- leaderboard eligibility
- broad model ranking
- fully solved vulnerable tasks; vulnerable full-pass count remains `0`

## Required Parent Verification

- `python3 scripts/validate_baseline_registry.py`
- `python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'`
- `python3 scripts/validate_v0_release.py --allow-incomplete`
- `python3 scripts/validate_public.py --include-scripted-baseline`
- privacy check proving raw panel logs, private holdouts, results, and captures
  are untracked
- remote CI after push
