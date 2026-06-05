# Opus Current Baseline Panel Context

Date: 2026-06-05

Section: baseline methodology and leaderboard schema

Scope: two Kiro `claude-opus-4.6` no-tools runs on the current 44-task public
split.

## Parent-Verified Facts

- Repo claim remains alpha / pre-v0.
- Public task split remains 44 tasks: 18 vulnerable, 26 controls, 10
  authorized-allow controls.
- Local ignored private holdouts exist, but private holdout JSON is not tracked
  and must not be included in public docs.
- The strict v0 gate still reports `v0_ready: false`.
- The Opus runs were executed at benchmark commit
  `3d95ab1fd1a20cbaafafdecc8d4514096cefa424`. Current HEAD has only moved
  forward for README/image cleanup since that run.
- Baseline registry now reports:
  - `baseline_count: 10`
  - `current_public_model_family_count: 5`
  - `repeated_model_baseline_count: 5`
  - `has_current_public_tool_agent_baseline: false`
  - `v0_baseline_ready: false`

## Opus Run Results

Run 1:

- Summary path:
  `baselines/kiro-claude-opus-4.6-current-public-44-run1-summary.json`
- Run id: `20260605T170620628460Z-00ecf889`
- Public tasks: 44
- Passed: 27
- Exploit-proven vulnerable tasks: 12 of 18
- Vulnerable full-pass count: 1 of 18
- Boundary reasoning pass rate: 0.0556
- False-positive rate: 0.0
- Authorized-allow pass rate: 1.0
- Model output parse errors: 2
- Model command failures: 0

Run 2:

- Summary path:
  `baselines/kiro-claude-opus-4.6-current-public-44-run2-summary.json`
- Run id: `20260605T171101075150Z-55f8db80`
- Public tasks: 44
- Passed: 27
- Exploit-proven vulnerable tasks: 12 of 18
- Vulnerable full-pass count: 1 of 18
- Boundary reasoning pass rate: 0.0556
- False-positive rate: 0.0
- Authorized-allow pass rate: 1.0
- Model output parse errors: 3
- Model command failures: 0

Both summaries intentionally omit raw task arrays, ignored result directories,
stdout/stderr, private holdouts, captures, and personal information. They are
public-split evidence only and are not leaderboard eligible.

## Files Updated for This Slice

- `baselines/baseline-registry.json`
- `baselines/kiro-claude-opus-4.6-current-public-44-run1-summary.json`
- `baselines/kiro-claude-opus-4.6-current-public-44-run2-summary.json`
- `README.md`
- `baselines/README.md`
- `docs/status.md`
- `docs/launch-report.md`
- `docs/baseline-credibility.md`
- `CHANGELOG.md`
- `tests/test_baseline_registry.py`

After review, `docs/reviews/review-registry.json` should list the accepted
Opus panel summary and say five repeated public no-tools families now exist.

## Verification Already Run

```bash
python3 -m json.tool baselines/baseline-registry.json >/dev/null
python3 -m json.tool baselines/kiro-claude-opus-4.6-current-public-44-run1-summary.json >/dev/null
python3 -m json.tool baselines/kiro-claude-opus-4.6-current-public-44-run2-summary.json >/dev/null
python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_v0_release.py --allow-incomplete
```

## Review Questions

1. Does the registry/doc update honestly count Opus as the fifth repeated
   current public model family without implying v0 or leaderboard readiness?
2. Are the Opus metrics explained accurately enough, especially the tension
   between 12 exploit-proven replays and only 1 full vulnerable-task pass?
3. Are there stale docs or wording that still says only four repeated current
   families or one family remaining?
4. Are there public-safety issues in the summary/docs, such as raw result paths,
   private holdout details, stdout/stderr, local filesystem paths, or personal
   information?
5. What concrete fixes are needed before this slice should be committed?
