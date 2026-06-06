# Tool-Agent Repeat Panel Summary

Date: 2026-06-06

Scope: second current-public live HTTP Kiro `claude-sonnet-4.6` tool-agent run,
baseline registry update, generated chart data, and public claim wording.

## Counted Reviewers

- Gemini 3.5 Flash (High), verified by Antigravity CLI log
- Gemini 3.1 Pro (High), verified by Antigravity CLI log
- Kiro CLI `claude-opus-4.8`, verified by live model catalog and Kiro output
- ChatGPT sub-reviewer

Claude Sonnet 4.6 and Claude Opus 4.6 Antigravity labels were verified by logs
but did not return substantive review text for this checkpoint, so they are not
counted as substantive reviewers.

Raw prompts and logs are kept under ignored `docs/reviews/panel-logs/` and are
not part of the public release artifact.

## Consensus

Reviewers agreed that the second current-public tool-agent run can count as
repeated current-public tool-agent evidence because:

- the registry lists two distinct run artifacts with distinct run IDs
- both summaries have 46 public tasks, the same public task fingerprint, the
  same score policy and evidence contract, and the same agent/model labels
- both runs include 46/46 model-plan artifacts, 46/46 tool-probe artifacts, and
  46/46 target-request correlation
- the registry still reports `v0_baseline_ready: false` with only 3 of 5
  required repeated current model/agent families

## Accepted Caveat

The strongest reviewer caveat was that the paired tool-agent runs are not
same-SHA variance evidence. They span adjacent public-doc/test/tool-agent-tooling
commits. The registry and baseline credibility docs now make the comparability
basis explicit: matching task fingerprint, task count, score policy, evidence
contract, agent/model labels, and artifact contract.

## Claim Boundary

Supported claim:

`AuthZBench-SaaS has two current-public live HTTP tool-agent runs for the
claude-sonnet-4.6 Kiro adapter, with repeated per-task plan/probe artifacts and
target-request correlation on the 46-task public split.`

Unsupported claims:

- private-holdout tool-agent performance
- hosted leaderboard readiness
- v0 baseline readiness
- same-SHA variance evidence
- fully solved vulnerable workflow tasks; vulnerable full-pass count remains `0`

## Required Parent Verification

- `python3 scripts/validate_baseline_registry.py`
- `python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'`
- `python3 scripts/validate_public.py --include-scripted-baseline`
- `python3 scripts/validate_v0_release.py --allow-incomplete`
- privacy check proving raw panel logs, private holdouts, results, and captures
  are untracked
- remote CI after commit
