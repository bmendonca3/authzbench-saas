# Haiku Current Public 46-Task Baseline Panel Summary

Date: 2026-06-06

Scope: two `claude-haiku-4.5` no-tools Kiro runs on the current 46-task public
split, their public-safe baseline summaries, registry entry, charts, docs, and
baseline-registry tests.

## Counted Reviewers

- Gemini 3.5 Flash (High), verified by Antigravity CLI log
- Gemini 3.1 Pro (High), verified by Antigravity CLI log
- Kiro `claude-opus-4.8`, verified against the local Kiro model catalog and
  command log
- panel synthesis

Claude Sonnet 4.6 and Claude Opus 4.6 Antigravity labels propagated in logs but
did not return substantive review output, so they are not counted.

Raw prompts and logs are kept under ignored `docs/reviews/panel-logs/` and are
not part of the public release artifact.

## Consensus

Reviewers agreed that the Haiku checkpoint is safe to commit as an alpha/pre-v0
evidence improvement. It adds a second repeated current public no-tools model
family while keeping `v0_baseline_ready: false`.

Reviewers also agreed the evidence should not be framed as a model ranking:
Haiku showed some exploit-proof success, but both runs had
`boundary_reasoning_pass_rate: 0.0`, so neither run fully passed vulnerable
tasks.

## Verified Facts

- Run 1: 46 tasks, 26 passed, 5 exploit-proven vulnerable replays, false-positive
  rate `0.037`, boundary reasoning `0.0`.
- Run 2: 46 tasks, 27 passed, 1 exploit-proven vulnerable replay, false-positive
  rate `0.0`, boundary reasoning `0.0`.
- The paired runs span adjacent commits where chart/status wording changed; task
  manifests, apps, scorer, runner, and harness behavior did not change.
- Registry state: 2 of 5 current public model families, 2 of 5 repeated model
  baselines, no current public tool-agent baseline, `v0_baseline_ready: false`.

## Accepted Findings

1. The Haiku baseline list had a duplicate entry in `baselines/README.md`.

Disposition: accepted and fixed. The duplicate entry was removed; the remaining
entry keeps the adjacent-commit caveat.

2. The paired Haiku runs are acceptable as an intermediate alpha evidence
checkpoint but should not be treated as final strict-v0 evidence.

Disposition: accepted. The registry and docs state this is public-split,
no-tools evidence only, and the full v0 gate remains blocked until three more
current repeated model/agent families and one current public tool-agent baseline
exist.

3. Haiku run 2 reports one model-output parse error but zero invalid
submissions.

Disposition: accepted and clarified. The no-tools Kiro adapter records the parse
error in `model-output.json` but writes a normalized empty `findings` list, so
the scorer treats the task as a normal no-finding miss rather than a malformed
submission. The result schema now documents that adapter parse errors are tracked
separately from `invalid_submission`.

## Claim Boundary

Supported claim:

`AuthZBench-SaaS has two repeated current public no-tools model-family baselines
on the 46-task split.`

Unsupported claims:

- v0 release readiness
- hosted leaderboard readiness
- private-holdout ranking
- current public tool-agent baseline
- strong vulnerable-task solving by Haiku

## Verification

Required verification for this checkpoint:

- `python3 -Wd -m unittest discover -s tests`
- `python3 scripts/validate_baseline_registry.py`
- `python3 scripts/validate_v0_release.py --allow-incomplete`
- `python3 scripts/validate_public.py --include-scripted-baseline`
- privacy check proving raw panel logs, private holdouts, results, and captures
  are untracked
- remote CI after commit
