# Haiku Current Baseline Panel Context

Date: 2026-06-05

Section: baseline methodology and leaderboard schema

Scope: two Kiro `claude-haiku-4.5` no-tools runs on the current 44-task public
split.

## Parent-Verified Facts

- Repo claim remains alpha / pre-v0.
- Public task split remains 44 tasks: 18 vulnerable, 26 controls, 10
  authorized-allow controls.
- Local ignored private holdouts exist, but private holdout JSON is not tracked
  and must not be included in public docs.
- The strict v0 gate still reports `v0_ready: false`.
- Baseline registry now reports:
  - `baseline_count: 9`
  - `current_public_model_family_count: 4`
  - `repeated_model_baseline_count: 4`
  - `has_current_public_tool_agent_baseline: false`
  - `v0_baseline_ready: false`
- MiniMax and GLM runs were attempted, stopped for runtime, produced no final
  summary JSON, and are not counted as evidence.

## Haiku Run Results

Run 1:

- Summary path:
  `baselines/kiro-claude-haiku-4.5-current-public-44-run1-summary.json`
- Run id: `20260605T165101168598Z-8e695864`
- Public tasks: 44
- Passed: 26
- Exploit-proven vulnerable tasks: 4 of 18
- Vulnerable full-pass count: 0 of 18
- Boundary reasoning pass rate: 0.0
- False-positive rate: 0.0
- Authorized-allow pass rate: 1.0
- Model output parse errors: 1

Run 2:

- Summary path:
  `baselines/kiro-claude-haiku-4.5-current-public-44-run2-summary.json`
- Run id: `20260605T165405378845Z-2d97bcff`
- Public tasks: 44
- Passed: 26
- Exploit-proven vulnerable tasks: 4 of 18
- Vulnerable full-pass count: 0 of 18
- Boundary reasoning pass rate: 0.0
- False-positive rate: 0.0
- Authorized-allow pass rate: 1.0
- Model output parse errors: 0

Both summaries intentionally omit raw task arrays, ignored result directories,
stdout/stderr, private holdouts, captures, and personal information.

## Files Updated for This Slice

- `baselines/baseline-registry.json`
- `baselines/kiro-claude-haiku-4.5-current-public-44-run1-summary.json`
- `baselines/kiro-claude-haiku-4.5-current-public-44-run2-summary.json`
- `README.md`
- `baselines/README.md`
- `docs/status.md`
- `docs/launch-report.md`
- `docs/baseline-credibility.md`
- `CHANGELOG.md`
- `tests/test_baseline_registry.py`

## Verification Already Run

```bash
python3 -m json.tool baselines/baseline-registry.json >/dev/null
python3 -m json.tool baselines/kiro-claude-haiku-4.5-current-public-44-run1-summary.json >/dev/null
python3 -m json.tool baselines/kiro-claude-haiku-4.5-current-public-44-run2-summary.json >/dev/null
python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_v0_release.py --allow-incomplete
```

## Review Questions

1. Does the registry/doc update honestly count Haiku as one additional repeated
   current public model family without implying v0 or leaderboard readiness?
2. Are the Haiku metrics explained accurately enough, especially the tension
   between four exploit-proven replays and zero full vulnerable passes?
3. Are there stale docs or wording that still says only three repeated current
   families or two families remaining?
4. Are there public-safety issues in the summary/docs, such as raw result paths,
   private holdout details, stdout/stderr, local filesystem paths, or personal
   information?
5. What concrete fixes are needed before this slice should be committed?
