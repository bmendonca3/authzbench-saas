# Tool-Agent Artifact Summary Panel Summary

Date: 2026-06-06

Scope: runner support for optional tool-agent plan/probe artifacts,
protected-private telemetry parity, Kiro live-tool planner timeout handling,
result-schema documentation, and focused tests.

## Counted Reviewers

- Gemini 3.5 Flash (High), verified by Antigravity CLI log
- Gemini 3.1 Pro (High), verified by Antigravity CLI log
- Post-fix Gemini 3.5 Flash (High) and Gemini 3.1 Pro (High), verified by
  Antigravity CLI logs
- Kiro CLI `claude-opus-4.8`, verified against the live Kiro model catalog
- ChatGPT subagent reviewer
- Parent ChatGPT synthesis

Claude Sonnet 4.6 and Claude Opus 4.6 Antigravity labels propagated in logs but
did not return substantive review output, so they are not counted.

Raw prompts and logs are kept under ignored `docs/reviews/panel-logs/` and are
not part of the public release artifact.

## Findings And Fixes

Reviewers agreed the runner change improves evidence quality but should not be
committed until surrounding contracts were aligned.

Accepted fixes:

- documented the new optional tool-agent fields in `docs/result-schema.md`
- aligned `scripts/protected_private_eval.py` with the public runner's
  tool-agent telemetry names
- aligned protected-private optional per-task probe fields with the public
  runner's omit-when-absent behavior
- made protected-private optional tool artifacts non-fatal when malformed
- added malformed optional-artifact and planner telemetry assertions in
  `tests/test_runner.py`
- added protected-private malformed optional-artifact coverage in
  `tests/test_protected_private_eval.py`
- added Kiro planner timeout fallback coverage in
  `tests/test_kiro_live_tool_agent.py`
- tightened the review registry baseline note so review coverage is not confused
  with completion of the current public model-family and tool-agent-baseline
  prerequisites

## Claim Boundary

Supported claim:

`The runner can now summarize optional tool-agent plan/probe artifacts and
probe telemetry without making auxiliary artifacts part of scoring.`

Unsupported claims:

- current public tool-agent baseline exists
- v0 baseline gate is complete
- self-reported probe/finding counters are scorer-owned evidence
- planner failure count captures every possible tool-agent failure mode; it only
  counts nonzero planner return codes from parseable plan artifacts

## Verification

Parent-verified before commit:

- `python3 -Wd -m unittest discover -s tests -p 'test_*.py'`
- `python3 scripts/validate_baseline_registry.py`
- `python3 scripts/validate_v0_release.py --allow-incomplete`
- `python3 scripts/validate_protected_private_evidence.py --summary 'docs/protected-private*-2026-06-05.redacted.json'`
- `python3 scripts/validate_public.py --include-scripted-baseline`
- `git diff --check`
- privacy checks for tracked private/raw artifacts and personal/secret strings
