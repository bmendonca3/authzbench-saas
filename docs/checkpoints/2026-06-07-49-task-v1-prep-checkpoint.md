# Historical 49-Task v1-Prep Checkpoint

This file preserves the detailed 49-task checkpoint record that previously
lived at the top of `docs/goal.md`. The active roadmap now lives in
`docs/goal.md`; this checkpoint is historical evidence only and must not be
used as a current 54-task comparison.

## Historical 49-Task Perfection Pass

Status: preserved checkpoint record as of 2026-06-07. The active source of
truth is `Active v1 Readiness Goal` below.

This section records the verification state reached by the preceding 49-task
v1-prep checkpoint. It is intentionally retained for auditability, but its
baseline counts and commit evidence must not be read as the current 54-task
comparison state.

### Checkpoint Objective

Keep `main` honest as post-v0 active development: frozen v0.0 evidence remains
auditable, the 49-task v1-prep checkpoint remains inspectable, the active
54-task split does not treat those model runs as current, and every remaining
v1/community-benchmark gap is visible rather than implied away.

### Verification Checklist

- [x] Active goal/checklist in this file names the exact perfection criteria.
  Evidence: this section defines the pass objective, verification checklist, and
  open gaps that must remain unchecked until real evidence exists.
- [x] Docker smoke fails clearly when Docker CLI exists but the daemon is not
  available locally.
  Evidence: direct local call to `run_container_smoke(ROOT)` prints Docker client
  information and exits with `docker daemon is required for
  --include-container-smoke; start Docker and rerun validation` when the daemon
  socket is unavailable.
- [x] GitHub Actions no longer relies on the deprecated Node 20 default for
  JavaScript actions.
  Evidence: workflow opts into Node 24 and uses Node-24-native
  `actions/checkout@v6` and `actions/setup-python@v6`; GitHub Actions run
  `27083608925` passed on `main` with no Node 20 annotation in the watch output.
- [x] Focused tests for changed validation behavior pass.
  Evidence: `python3 -m unittest discover -s tests -p
  'test_validate_public.py'` and the full test suite pass.
- [x] Full public validation without local Docker smoke passes.
  Evidence: `python3 scripts/validate_public.py --include-scripted-baseline`
  passed on commit `ede97d01ecb708feb24985dec0fc3b51d37ac7d1` for the then-current
  49-task public split.
- [x] Docker-backed public validation is confirmed by GitHub Actions on `main`.
  Evidence: GitHub Actions run `27083952334` passed on `main` for commit
  `ede97d01ecb708feb24985dec0fc3b51d37ac7d1`.
- [x] Privacy scan shows no tracked private holdouts, raw results, captures, or
  panel logs.
  Evidence: `git ls-files tasks_private/holdout results captures
  docs/reviews/panel-logs` returns no tracked paths.
- [x] Tracked working tree is clean after generated validation artifacts are
  removed.
  Evidence: generated `results/validation-scripted-baseline/...` output was
  removed after validation, leaving no tracked working-tree changes before the
  pushed implementation commit.
- [x] Commit is authored as `bmendonca3` and pushed to `main`.
  Evidence: commit `ede97d01ecb708feb24985dec0fc3b51d37ac7d1` is authored and
  committed as `bmendonca3 <bmendonca3@users.noreply.github.com>` and is present
  on both `origin/main` and `origin/v1-task-expansion`.
- [x] The 49-task checkpoint had one repeated no-tools model-family baseline.
  Evidence: `kiro-claude-haiku-4-5-current-public-49` is registered with two
  then-current public split Haiku runs, `task_count: 49`, `run_count: 2`,
  `harness_type: no-tools-model`, and explicit non-leaderboard claim-boundary
  text.
- [x] The 49-task checkpoint had five repeated no-tools model families.
  Evidence: `kiro-claude-haiku-4-5-current-public-49`,
  `kiro-claude-sonnet-4-6-current-public-49`,
  `kiro-qwen3-coder-next-current-public-49`, `kiro-glm-5-current-public-49`,
  and `kiro-claude-opus-4-6-current-public-49` were registered as current public
  split no-tools model baselines at that checkpoint, with `run_count: 2`, distinct
  `run_artifacts`, `task_count: 49`, matching model labels, benchmark commit
  `1eaac973ffe5229dad5796b9a5b144fa3af37a3a`, and non-leaderboard
  claim-boundary notes.
- [x] The 49-task checkpoint had repeated live HTTP tool-agent runs with
  target-request correlation.
  Evidence: `kiro-live-tool-agent-sonnet-current-public-49` was registered as a
  current public split tool-agent baseline at that checkpoint, with two
  `claude-sonnet-4.6` Kiro live HTTP runs from benchmark commit
  `3d4293cd24305ad410ddad8cb68654bf10adc9ff`. Run
  `20260607T071431380750Z-fc6636f1` reports `task_count: 49`,
  `model_tool_plan_artifact_count: 49`, `per_task_tool_probe_artifact_count:
  49`, `target_request_correlated_task_count: 49`,
  `target_request_coverage_rate: 1.0`, `planner_failure_count: 0`,
  `planner_parse_error_count: 0`, and `executed_tool_probe_total: 124`. Run
  `20260607T072056877797Z-2be17ca0` reports the same 49/49 artifact and
  correlation counts, `target_request_coverage_rate: 1.0`, zero planner/parser
  failures, and `executed_tool_probe_total: 126`.
- [x] Baseline registry and release gates recognized the 49-task checkpoint.
  Evidence: `python3 scripts/validate_baseline_registry.py` passes with
  `baseline_count: 23`, `current_public_model_family_count: 6`,
  `repeated_model_baseline_count: 6`, `has_current_public_tool_agent_baseline:
  true`, `v0_baseline_ready: true`, `v0_release_snapshot_ready: true`, and no
  unmet baseline requirements. Strict `python3 scripts/validate_v0_release.py`
  passes with all 8 gates green and `v0_ready: true` in this maintainer checkout.
- [x] The 49-task public tool-agent checkpoint was committed, pushed, and CI
  verified.
  Evidence: commit `fd0bfcb41e0f8db0b52a0a7f56106c9c2e2e416b` (`Add current
  public tool-agent baseline evidence`) is authored as `bmendonca3`, pushed to
  both `origin/v1-task-expansion` and `origin/main`, and GitHub Actions run
  `27086361745` passed the `Validate AuthZBench-SaaS` workflow on `main`.

### Open Perfection Gaps

These remain intentionally open until real evidence exists:

- [x] Boundary-reasoning calibration study completed and reflected in the paper.
  Evidence: `docs/boundary-reasoning-calibration-study.md` audits both
  then-current 49-task live HTTP `claude-sonnet-4.6` tool-agent runs, covering all 30
  exploit-proven vulnerable task-run cases where boundary reasoning failed.
  `docs/authzbench-saas-v1-prep-technical-report.md` and
  `paper/ieee-sp/main.tex` now state the calibrated interpretation: exploit
  replay often succeeded, but submitted boundaries did not preserve the
  oracle-compatible vocabulary required by `score-policy-v1`.
- [ ] External AppSec, benchmark/evals, and AI-agent/tooling review lanes
  completed.
- [x] Rotating private holdout and hosted or fully containerized submission
  governance defined for v1/community use.
  Evidence: `docs/v1-community-submission-governance.md` defines submission
  states, eligibility gates, hosted-runner flow, fully containerized flow,
  private-pack rotation, stale-score handling, tie policy, attestation,
  appeals, deprecation, and the minimum v1 launch bar. It links to
  `docs/holdout-rotation-protocol.md` and `artifact/run-bundle.md` while
  preserving the claim boundary that hosted/containerized execution is specified
  but not yet implemented.

### Externally Blocked Gap

- External review remains open. Evidence packet:
  `docs/reviews/external-review-packet.md`. Tracker:
  `docs/reviews/external-review-summary.md`. Blocker: completion requires real
  independent AppSec, benchmark/evals, and AI-agent/tooling reviewers to return
  findings or explicit no-finding dispositions; local repository work cannot
  honestly manufacture that evidence.
- Release-grade hosted/containerized execution also remains infrastructure
  dependent. Repository and CI work can prove the submitter-isolation mechanism
  with a rehearsal pack, but the release gate requires the same path to run on
  the intended maintainer platform against the real active private-pack
  fingerprint. Rehearsal evidence must not be promoted into release evidence.
