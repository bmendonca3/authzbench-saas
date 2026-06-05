# Baseline Registry Panel Context

Date: 2026-06-05

Section: baseline methodology and leaderboard schema.

## Review Question

Does the new baseline registry make AuthZBench-SaaS more credible as an
alpha/pre-v0 benchmark without overclaiming v0, leaderboard, or top-benchmark
readiness?

## Changed Files

- `scripts/validate_baseline_registry.py`
- `baselines/baseline-registry.json`
- `tests/test_baseline_registry.py`
- `scripts/validate_public.py`
- `tests/test_validate_public.py`
- `docs/baseline-credibility.md`
- `baselines/README.md`
- `README.md`
- `ROADMAP.md`
- `docs/status.md`
- `docs/v0-release-plan.md`
- `docs/leaderboard-schema.md`
- `docs/benchmark-card.md`
- `docs/publish-checklist.md`
- `docs/launch-report.md`
- `CHANGELOG.md`

## Parent-Verified Facts

- Current public split validates as 44 tasks:
  - 18 vulnerable tasks
  - 26 secure controls
  - 16 denial controls
  - 10 authorized-allow controls
- The baseline registry contains 4 tracked summaries:
  - 1 current 44-task deterministic scripted harness check
  - 1 legacy 15-task live scripted harness snapshot
  - 2 legacy 15-task no-tools Kiro model snapshots
- The registry validator passes while reporting `v0_baseline_ready: false`.
- Current unmet v0 baseline requirements:
  - current public model families: 0 of 5
  - repeated model baselines: 0 of 5
  - missing current public tool-agent baseline
- The public validation gate now runs `scripts/validate_baseline_registry.py`.
- The validator rejects:
  - legacy snapshots mislabeled as current public split
  - one-off model baselines marked leaderboard eligible
  - inflated repeated-run counts without a `run_artifacts` list
  - model baselines labeled as current public harness checks
  - harness checks marked leaderboard eligible

## Independent Audit Disposition

An independent ChatGPT subagent reviewed the uncommitted baseline credibility
slice and found four actionable issues.

Accepted and fixed:

- Repeated-run/leaderboard eligibility previously trusted self-declared
  `run_count`; validator now requires matching existing `run_artifacts` for
  repeated or leaderboard baselines.
- A model baseline could previously use `current_public_harness_check`;
  validator now restricts that label to `harness_check` entries.
- `baselines/README.md` previously described Kiro snapshots as full public
  split; wording now says legacy 15-task alpha snapshots.
- `docs/launch-report.md` previously said initial public-split model baselines;
  wording now says initial legacy 15-task public-alpha model snapshots.

## Verification Run

Focused checks after fixes:

```bash
python3 -Wd -m unittest discover -s tests -p 'test_baseline_registry.py'
python3 -Wd -m unittest discover -s tests -p 'test_validate_public.py'
python3 scripts/validate_baseline_registry.py
git diff --check
```

Results:

- `test_baseline_registry.py`: 5 tests passed
- `test_validate_public.py`: 4 tests passed
- registry validator: passed, `v0_baseline_ready: false`
- diff check: passed

Full local gate:

```bash
python3 scripts/validate_public.py --include-scripted-baseline
```

Results:

- 61 tests passed
- manifest validation passed
- baseline registry validation passed
- compile checks passed
- Docker Compose config passed
- Git-tracked privacy scan passed
- deterministic scripted baseline passed 44/44

Note: the scripted validation summary still reports the previous commit SHA
because this section has not been committed yet. The full validation should be
rerun after commit so the summary uses the new commit SHA.

## Known Remaining v0 Gaps

- No real private holdout pack is committed or exposed; real private holdouts
  must remain outside public Git history.
- Protected private-holdout execution is not implemented.
- Private route/decoy variation is validated for rehearsal packs but not yet
  implemented as real maintainer-run holdouts.
- Current public model baselines have not been rerun on the 44-task split.
- No current public tool-agent baseline exists.
- No final release-readiness panel has declared the benchmark v0-ready.
