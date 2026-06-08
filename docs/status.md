# Release Status

Last updated: 2026-06-08

## v1 Prep Status

v1 work has started as planning and readiness work only. The source of truth for
the startup gate is `docs/v1-readiness-checklist.md`.

Current v1-prep boundary:

- v0.0 remains frozen historical release evidence.
- `main` is post-v0 active development and carries billing-entitlement plus
  support-reassignment task slices, expanding the public task set to 54 tasks.
- Old 46-task baselines are stale for v1 comparison until rerun against the
  expanded public split.
- The preceding 49-task split has five repeated no-tools Kiro model families
  and one repeated live HTTP Kiro tool-agent family with 49/49 target-request
  correlation in both runs. All are stale for current 54-task comparison.
- v1-prep does not imply hosted leaderboard operation, v1 release readiness, or
  community-scale benchmark maturity.

Current main / v1-prep split:

- 54 public task manifests
- 21 vulnerable tasks
- 33 secure-control tasks
- 19 denial controls and 14 authorized-allow controls
- one current 54-task deterministic scripted sanity baseline
- five current repeated 54-task no-tools model-family baselines: Qwen with
  model-output failure diagnostics, Claude Haiku 4.5 with complete zero-failure
  task artifacts, Claude Sonnet 4.6 with complete zero-failure task artifacts
  and runner-emitted finding totals, GLM-5 with retained runner-failure
  diagnostics in one run and a clean retry run, and Claude Opus 4.6 with
  complete zero-failure task artifacts
- one current repeated 54-task live HTTP Kiro `claude-sonnet-4.6` tool-agent
  baseline with 54/54 target-request correlation in both runs
- five repeated 49-task no-tools Kiro model-family baselines, now stale
- one repeated 49-task live HTTP Kiro tool-agent baseline, now stale

## Current v1-Prep Public Split And Frozen v0.0 Snapshot

AuthZBench-SaaS currently contains a 54-task public split on `main`. The v0.0
release snapshot remains frozen at 46 public tasks and is preserved in the
baseline registry as historical evidence.

### Current main / v1-prep split

- 6 Dockerized synthetic SaaS targets
- 54 public task manifests
- 21 vulnerable tasks
- 33 secure-control tasks
- 19 denial controls and 14 authorized-allow controls
- one current deterministic scripted harness check
- five current repeated 54-task no-tools Kiro model baselines:
  `qwen3-coder-next`, with explicit model-output failure diagnostics, and
  `claude-haiku-4.5`, with zero adapter, runner, and invalid-submission failures;
  and `claude-sonnet-4.6`, with zero adapter, runner, and invalid-submission
  failures; and `glm-5`, with one retained outer runner failure in run 1 and
  complete zero-failure artifacts in run 2; and `claude-opus-4.6`, with
  complete zero-failure artifacts in both runs; public-split evidence only
- five stale 49-task no-tools Kiro model-family baselines
- one stale 49-task live HTTP Kiro tool-agent baseline with 49/49 target-request
  correlation in both historical runs
- seeded runtime fixtures for tenant, object, organization, invoice, file, link,
  workspace, API-token, scope, and actor IDs
- route aliases and decoy controls across all six target apps
- target-side JSONL request logs for Docker HTTP targets
- alpha runner correlation into per-task `target-requests.jsonl` artifacts when
  `--target-log-dir` is supplied
- deterministic scorer with backend replay transcripts
- v0 evidence run-summary metrics for exploit proof, boundary reasoning,
  secure-control false reports, secure-control execution, and target-request
  coverage, plus invalid-submission tracking
- result and leaderboard schema documentation
- public holdout strategy documentation
- v0 task build matrix documentation
- baseline registry validation that separates harness checks, legacy snapshots,
  current public split summaries, frozen release snapshots, and leaderboard
  eligibility
- current 54-task deterministic scripted harness check
- repeated current 54-task no-tools Kiro `qwen3-coder-next` model baseline
- repeated current 54-task no-tools Kiro `claude-haiku-4.5` model baseline
- repeated current 54-task no-tools Kiro `claude-sonnet-4.6` model baseline
- repeated current 54-task no-tools Kiro `glm-5` model baseline
- repeated current 54-task no-tools Kiro `claude-opus-4.6` model baseline
- repeated current 54-task live HTTP Kiro `claude-sonnet-4.6` tool-agent
  baseline with per-task plan/probe artifacts and 54/54 target-request
  correlation
- repeated stale 49-task no-tools Kiro `claude-haiku-4.5` model baseline
- repeated stale 49-task no-tools Kiro `claude-sonnet-4.6` model baseline
- repeated stale 49-task no-tools Kiro `qwen3-coder-next` model baseline
- repeated stale 49-task no-tools Kiro `glm-5` model baseline
- repeated stale 49-task no-tools Kiro `claude-opus-4.6` model baseline
- repeated stale 49-task live HTTP Kiro `claude-sonnet-4.6` tool-agent
  baseline with per-task plan/probe artifacts and 49/49 historical
  target-request correlation
- stale v0.0 46-task deterministic scripted harness check
- repeated stale v0.0 46-task no-tools Kiro `qwen3-coder-next` model baseline
- repeated stale v0.0 46-task no-tools Kiro `claude-haiku-4.5` model baseline
- repeated stale v0.0 46-task no-tools Kiro `claude-sonnet-4.6` model baseline
- repeated stale v0.0 46-task no-tools Kiro `glm-5` model baseline
- repeated stale v0.0 46-task live HTTP Kiro `claude-sonnet-4.6` tool-agent baseline with
  per-task plan/probe artifacts and 46/46 target-request correlation
- stale 44-task live HTTP scripted, heuristic, model, and tool-agent summaries
  retained as context until rerun on the current split
- v0 release-gate audit script that reports strict readiness from the current
  evidence state, including explicit unmet gates when a section is incomplete
- release evidence registry for local validation, fresh-clone validation, remote
  CI, Docker smoke, privacy scan, release-note separation, and protected
  private-holdout execution
- repeated protected-private redacted evidence validation, including a no-tools
  private run and a live tool-agent private run with target-request coverage
- validated private-holdout release-candidate leaderboard evidence summarized at
  aggregate level only
- leaderboard submission validation with a tracked public harness-check example
  that is schema-valid, cross-checked against a source run summary, and not
  leaderboard eligible
- GitHub Actions workflow for public validation gates, including Docker runtime
  smoke

### Frozen v0.0 release snapshot

- 46 public task manifests
- 19 vulnerable tasks
- 27 secure-control tasks
- 16 denial controls and 11 authorized-allow controls
- historical 46-task scripted and model/tool-agent baseline summaries retained
  for v0.0 auditability
- 46-task baseline rows are stale for current 54-task comparison until rerun

## Verified Locally

The following checks have been run successfully for the released v0.0 scaffold.
Public-only checkouts can use `--allow-incomplete` because private holdouts are
intentionally absent from public Git history:

```bash
python3 -Wd -m unittest discover -s tests
python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_v0_release.py --allow-incomplete
python3 scripts/validate_leaderboard_submission.py --submission 'examples/leaderboard/*.json' --require-source-summary
python3 -m compileall -q authzbench apps tests scripts
python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/scripted_baseline_agent.py' --results-dir results/scripted-baseline --timeout-seconds 10 --benchmark-commit-sha "$(git rev-parse HEAD)" --agent scripted_baseline_agent --model deterministic-script --harness-type scripted
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/validate_public.py --include-scripted-baseline --include-container-smoke
```

The frozen v0.0 release snapshot remains baseline-ready. The five repeated
no-tools model families plus one repeated live HTTP tool-agent family for the
49-task public split are now stale after the 54-task expansion. The current
public-split baseline bar has been restored for five no-tools model families
and one live HTTP tool-agent family on the 54-task fingerprint. Strict
`python3 scripts/validate_v0_release.py` should be rerun in a maintainer
checkout before future tags because release evidence and CI references are
time-sensitive.

The legacy Kiro baseline snapshots were run on the earlier 15-task split and
are retained only as historical context. Docker runtime smoke requires a Docker
daemon; the `--include-container-smoke` path validates Docker Compose config,
starts the target stack, checks request logs, and is covered by the GitHub
Actions public-validation workflow.
The deterministic scripted baseline was rerun on the v0.0 46-task public split.
The `qwen3-coder-next`, `claude-haiku-4.5`, `claude-sonnet-4.6`, and `glm-5`
no-tools Kiro baselines were each rerun twice on that 46-task split. Those rows
are now stale for current 54-task comparison. The older live HTTP scripted,
heuristic, and older Kiro model/tool-agent summaries remain stale 44-task
snapshots because earlier public splits changed. The v0.0
`claude-sonnet-4.6` live HTTP tool-agent baseline has two 46-task public-split
runs with per-task plan/probe artifacts and full target-request correlation in
both runs, but it is still not private-holdout or hosted leaderboard evidence.
The second Qwen run also had one invalid submission on a vulnerable task
(`invalid_submission_rate: 0.0217`), so the v0.0 Qwen evidence should be read
as repeatability evidence, not a polished model ranking.

The stale 49-task no-tools Kiro baselines have two runs each for
`claude-haiku-4.5`, `claude-sonnet-4.6`, `qwen3-coder-next`, `glm-5`, and
`claude-opus-4.6`. They are public-split diagnostic evidence only: all five
families still have `boundary_reasoning_pass_rate: 0.0`, and none are
private-holdout, tool-agent, hosted-leaderboard, or v1 release evidence.

The stale 49-task live HTTP Kiro `claude-sonnet-4.6` tool-agent baseline has
two runs with one model-plan artifact and one tool-probe artifact per task,
49/49 target-request correlation in both runs, zero planner failures, and zero
parser failures. Both runs proved 15 of 20 vulnerable replays and produced zero
secure-control false reports, but vulnerable boundary reasoning remained
`0.0`, so no vulnerable task fully passed. It is still public-split diagnostic
evidence only, not private-holdout, hosted-leaderboard, or v1 release evidence.

The current 54-task live HTTP Kiro `claude-sonnet-4.6` tool-agent baseline has
two runs with one model-plan artifact and one tool-probe artifact per task,
54/54 target-request correlation in both runs, zero planner failures, zero
parser failures, zero invalid submissions, and zero secure-control false
reports. Both runs pass 33 tasks, prove 15 of 21 vulnerable replays, and keep
boundary reasoning at `0.0`, so no vulnerable task fully passes. This restores
the active public tool-agent evidence bar, but remains public-split diagnostic
evidence only, not private-holdout, hosted-leaderboard, or v1 release evidence.

## Baseline Results

| Baseline | Tasks | Passed | Exploit-proven success | Boundary reasoning | False-positive rate | Authorized-allow pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Scripted sanity baseline, current v1-prep split | 54 | 54 | 1.0 | 1.0 | 0.0 | 1.0 |
| Kiro `qwen3-coder-next` no-tools current 54-task run 1 | 54 | 32 | 0.0 | 0.0 | 0.0303 | 1.0 |
| Kiro `qwen3-coder-next` no-tools current 54-task run 2 | 54 | 33 | 0.1429 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-haiku-4.5` no-tools current 54-task run 1 | 54 | 32 | 0.1905 | 0.0 | 0.0303 | 0.9286 |
| Kiro `claude-haiku-4.5` no-tools current 54-task run 2 | 54 | 32 | 0.2381 | 0.0 | 0.0303 | 0.9286 |
| Kiro `claude-sonnet-4.6` no-tools current 54-task run 1 | 54 | 32 | 0.7143 | 0.0 | 0.0303 | 0.9286 |
| Kiro `claude-sonnet-4.6` no-tools current 54-task run 2 | 54 | 32 | 0.6667 | 0.0 | 0.0303 | 1.0 |
| Kiro `glm-5` no-tools current 54-task run 1 | 54 | 33 | 0.0952 | 0.0 | 0.0 | 1.0 |
| Kiro `glm-5` no-tools current 54-task run 2 | 54 | 33 | 0.1429 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-opus-4.6` no-tools current 54-task run 1 | 54 | 33 | 0.6667 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-opus-4.6` no-tools current 54-task run 2 | 54 | 33 | 0.6667 | 0.0 | 0.0 | 1.0 |
| Kiro live HTTP tool-agent `claude-sonnet-4.6` current 54-task run 1 | 54 | 33 | 0.7143 | 0.0 | 0.0 | 1.0 |
| Kiro live HTTP tool-agent `claude-sonnet-4.6` current 54-task run 2 | 54 | 33 | 0.7143 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-haiku-4.5` no-tools stale 49-task run 1 | 49 | 29 | 0.3 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-haiku-4.5` no-tools stale 49-task run 2 | 49 | 29 | 0.15 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-sonnet-4.6` no-tools stale 49-task run 1 | 49 | 29 | 0.2 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-sonnet-4.6` no-tools stale 49-task run 2 | 49 | 29 | 0.2 | 0.0 | 0.0 | 1.0 |
| Kiro `qwen3-coder-next` no-tools stale 49-task run 1 | 49 | 28 | 0.05 | 0.0 | 0.0345 | 1.0 |
| Kiro `qwen3-coder-next` no-tools stale 49-task run 2 | 49 | 29 | 0.1 | 0.0 | 0.0 | 1.0 |
| Kiro `glm-5` no-tools stale 49-task run 1 | 49 | 29 | 0.15 | 0.0 | 0.0 | 1.0 |
| Kiro `glm-5` no-tools stale 49-task run 2 | 49 | 28 | 0.1 | 0.0 | 0.0345 | 1.0 |
| Kiro `claude-opus-4.6` no-tools stale 49-task run 1 | 49 | 29 | 0.55 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-opus-4.6` no-tools stale 49-task run 2 | 49 | 29 | 0.55 | 0.0 | 0.0 | 1.0 |
| Kiro live HTTP tool-agent `claude-sonnet-4.6` stale 49-task run 1 | 49 | 29 | 0.75 | 0.0 | 0.0 | 1.0 |
| Kiro live HTTP tool-agent `claude-sonnet-4.6` stale 49-task run 2 | 49 | 29 | 0.75 | 0.0 | 0.0 | 1.0 |
| Scripted sanity baseline, stale v0.0 snapshot | 46 | 46 | 1.0 | 1.0 | 0.0 | 1.0 |
| Kiro `qwen3-coder-next` no-tools stale v0.0 run 1 | 46 | 27 | 0.0 | 0.0 | 0.0 | 1.0 |
| Kiro `qwen3-coder-next` no-tools stale v0.0 run 2 | 46 | 27 | 0.0526 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-haiku-4.5` no-tools stale v0.0 run 1 | 46 | 26 | 0.2632 | 0.0 | 0.037 | 1.0 |
| Kiro `claude-haiku-4.5` no-tools stale v0.0 run 2 | 46 | 27 | 0.0526 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-sonnet-4.6` no-tools stale v0.0 run 1 | 46 | 27 | 0.6316 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-sonnet-4.6` no-tools stale v0.0 run 2 | 46 | 26 | 0.4211 | 0.0 | 0.037 | 1.0 |
| Kiro `glm-5` no-tools stale v0.0 run 1 | 46 | 27 | 0.2105 | 0.0 | 0.0 | 1.0 |
| Kiro `glm-5` no-tools stale v0.0 run 2 | 46 | 27 | 0.0526 | 0.0 | 0.0 | 1.0 |
| Kiro live HTTP tool-agent `claude-sonnet-4.6` stale v0.0 run 1 | 46 | 27 | 0.7368 | 0.0 | 0.0 | 1.0 |
| Kiro live HTTP tool-agent `claude-sonnet-4.6` stale v0.0 run 2 | 46 | 27 | 0.7368 | 0.0 | 0.0 | 1.0 |
| Live HTTP scripted baseline, stale 44-task snapshot | 44 | 44 | 1.0 | 1.0 | 0.0 | 1.0 |
| Heuristic live HTTP prober, stale 44-task snapshot | 44 | 33 | 0.6111 | 0.6667 | 0.0 | 1.0 |
| Kiro `claude-sonnet-4.6` no-tools legacy snapshot | 15 | 11 | 0.3333 | not tracked | 0.0 | not tracked |
| Kiro `qwen3-coder-next` no-tools legacy snapshot | 15 | 8 | 0.0 | not tracked | 0.1111 | not tracked |
| Kiro `claude-opus-4.6` no-tools stale run 1 | 44 | 27 | 0.6667 | 0.0556 | 0.0 | 1.0 |
| Kiro `claude-opus-4.6` no-tools stale run 2 | 44 | 27 | 0.6667 | 0.0556 | 0.0 | 1.0 |
| Kiro `claude-sonnet-4.6` no-tools stale run 1 | 44 | 29 | 0.7778 | 0.1667 | 0.0 | 1.0 |
| Kiro `claude-sonnet-4.6` no-tools stale run 2 | 44 | 29 | 0.7778 | 0.1667 | 0.0 | 1.0 |
| Kiro `claude-haiku-4.5` no-tools stale run 1 | 44 | 26 | 0.2222 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-haiku-4.5` no-tools stale run 2 | 44 | 26 | 0.2222 | 0.0 | 0.0 | 1.0 |
| Kiro `deepseek-3.2` no-tools stale run 1 | 44 | 26 | 0.0 | 0.0 | 0.0 | 1.0 |
| Kiro `deepseek-3.2` no-tools stale run 2 | 44 | 26 | 0.0 | 0.0 | 0.0 | 1.0 |
| Kiro `qwen3-coder-next` no-tools stale run 1 | 44 | 26 | 0.0 | 0.0 | 0.0 | 1.0 |
| Kiro `qwen3-coder-next` no-tools stale run 2 | 44 | 25 | 0.0 | 0.0 | 0.0385 | 1.0 |
| Kiro live HTTP tool-agent `claude-sonnet-4.6` stale 44-task snapshot | 44 | 26 | 0.7778 | 0.0 | 0.0 | 1.0 |

For current Qwen run 1, `false_positive_rate: 0.0303` means one of 33 secure
controls failed because the outer runner produced an invalid submission.
`control_false_report_rate` is `0.0`: the model did not submit a finding on a
secure control. Inner Kiro command or JSON-extraction failures are separately
counted as task-level adapter diagnostics; the adapter's empty-findings fallback
remains in the scored denominator.

The current Claude Haiku 4.5 pair passes 32 tasks in both runs, proves 4 and 5
of 21 vulnerable replays, keeps boundary reasoning at `0.0`, and fully passes
no vulnerable task. Both runs have zero adapter failures, zero outer runner
failures, and zero invalid submissions. Each reports one false finding on the
authorized-allow support reassignment control, so both
`false_positive_rate` and `control_false_report_rate` are `0.0303`, while
`authorized_allow_pass_rate` is `0.9286`. This is current public diagnostic
evidence for a second no-tools family, not a stable cross-model ranking.

The current Claude Sonnet 4.6 pair also passes 32 tasks in both runs, proves 15
and 14 of 21 vulnerable replays, keeps boundary reasoning at `0.0`, and fully
passes no vulnerable task. Both runs have zero adapter failures, zero outer
runner failures, and zero invalid submissions. Run 1 reports the
authorized-allow admin reassignment control as vulnerable, producing
`authorized_allow_pass_rate: 0.9286`; run 2 reports the secure viewer-status
denial control as vulnerable while preserving `authorized_allow_pass_rate:
1.0`. Both therefore have `false_positive_rate` and
`control_false_report_rate` of `0.0303`. This is current public diagnostic
evidence for a third no-tools family, not a stable cross-model ranking.

The current GLM-5 pair passes 33 tasks in both runs, proves 2 and 3 of 21
vulnerable replays, keeps boundary reasoning at `0.0`, and fully passes no
vulnerable task. Both runs have zero control false reports and
`authorized_allow_pass_rate: 1.0`. Run 1 preserves one outer runner failure on
`sup_multistep_agent_status_then_admin_reassignment`, producing one invalid
submission and missing submission/model-output artifacts for that task; run 2
has complete 54-task artifacts and zero invalid submissions. This is current
public diagnostic evidence for a fourth no-tools family, not a stable
cross-model ranking.

The v0.0 Qwen repeat is useful because it shows variance, not because it is
a strong model result. Run 2 found one replay-proven vulnerable task but still
had `boundary_reasoning_pass_rate: 0.0` and one invalid vulnerable-task
submission; `v0_mean_score` remains a full-pass aggregate, separate from
partial-credit `mean_score`.
The v0.0 Haiku repeat adds a second v0.0 public no-tools model family. It
showed some exploit-proof success but still produced no fully passed vulnerable
tasks because vulnerable boundary reasoning remained `0.0`; run 1 also had one
secure-control false report.
The v0.0 Sonnet no-tools repeat adds a third v0.0 public no-tools model
family. It proved stronger vulnerable replay evidence than Qwen or Haiku in
these public runs, but still produced no fully passed vulnerable tasks because
vulnerable boundary reasoning remained `0.0`; run 2 also had one secure-control
false report.
The v0.0 GLM repeat adds a fourth v0.0 public no-tools model family and
the fifth repeated v0.0 model/agent family overall when counted with the
tool-agent family. It produced 1-4 exploit-proven vulnerable replays per run,
zero fully passed vulnerable tasks, and zero secure-control false reports.

## Publication Readiness

Ready public v0.0 infrastructure:

This list is not a hosted-leaderboard claim. The baseline credibility sub-gate
has five repeated model/agent-family baselines for the frozen v0.0 release
snapshot. They are no longer current-comparable after the live public split
expanded to 54 tasks.

- public task manifests validate
- public docs explain task purpose, scoring, result artifacts, baselines, and limits
- tracked baseline summaries exist
- current 54-task deterministic scripted harness summary exists for the live
  v1-prep split
- five repeated current 54-task no-tools model-family baselines and one repeated
  current 54-task live HTTP tool-agent family exist on the active public split
- frozen v0.0 deterministic scripted harness summary exists for the 46-task
  release snapshot
- four repeated v0.0 no-tools model-family baselines and one repeated v0.0 live
  HTTP tool-agent family exist on the 46-task release snapshot
- one repeated v0.0 live HTTP tool-agent baseline exists on the 46-task release
  snapshot, with plan/probe artifacts and full target-request correlation
- five repeated 49-task no-tools model-family baselines and one repeated
  49-task live HTTP tool-agent family remain as stale historical evidence
- baseline registry exists and passes consistency validation while reporting
  `v0_baseline_ready: true` for the live 54-task public baseline bar and
  `v0_release_snapshot_ready: true` for the frozen v0.0 release snapshot
- stale 44-task heuristic and Kiro live HTTP summaries are retained for context,
  but they no longer count as current public comparison evidence
- repeated Kiro model-family summaries remain useful 44-task snapshots, but they
  require rerun before any current comparison or leaderboard claim
- v0 release-gate audit exists and is run in public validation with
  `--allow-incomplete`, so alpha validation can pass even when a future section
  is intentionally open
- strict v0 readiness also depends on `docs/release-evidence.json`; the release
  evidence checks now pass for the current release-candidate checkpoint
- the task-realism and vulnerable/control-mix review section is now v0-ready
  based on final task-mix panel review and aggregate validator evidence
- leaderboard submission validator exists and is part of public validation
- tracked leaderboard examples are cross-checked against source run summaries
  instead of trusting hand-entered aggregate rows
- leaderboard-eligible rows require source summaries plus both vulnerable-task
  and secure-control coverage
- two redacted private-holdout rows exist under `leaderboard_submissions/`: the
  older reconstructed historical row remains non-eligible, while the newer
  host-isolated no-tools row has runner-emitted fingerprint provenance and
  validates as release-candidate eligible
- `leaderboard-submission-v1` now binds every row to an eligibility-policy
  version, benchmark fingerprint, comparability key, and explicit source-run
  provenance
- reproducible fresh-clone validation script exists
- private holdout pack validator exists for ignored local holdouts, including
  app coverage, control subtype mix, public ID/seed overlap checks, private
  route/decoy variant metadata, and behavioral public-structure copy detection
- ignored local holdout rehearsal generator exists for maintainers to test the
  private-pack workflow without committing private JSON
- rehearsal manifests and validation output are machine-marked as not suitable
  for leaderboard scoring
- Git-tracked privacy scan exists in the public validation script
- private holdout JSON is excluded from the publishable repo
- protected private-holdout execution can optionally correlate live target
  request logs into per-task artifacts without exposing target-log paths to the
  agent workspace
- two redacted private execution summaries validate as repeated historical
  aggregate evidence without publishing private task rows or raw result
  bundles; they predate enforced host private-path denial
- the protected private runner now uses macOS `sandbox-exec` when available to
  deny agent reads of holdout and raw-evidence roots; fresh runs are required
  before this can support eligibility
- final holdout anti-gaming and final release-readiness review summaries exist
  and mark all required review-registry sections v0-ready
- local-status paths and personal filesystem references have been removed from this document

Still required before a hosted public leaderboard or v1/community claim:

- keep `docs/release-evidence.json` tied to exact command, commit, CI, and
  artifact evidence as later release checks are rerun
- post-push clone check from public `github.com` before future tags or releases
- independent AppSec, benchmark/evals, and AI-agent/tooling review dispositions
- hosted or fully containerized leaderboard execution if third-party submissions
  will be accepted at scale; governance is defined in
  `docs/v1-community-submission-governance.md`, but the runner path is not live
- rotating multi-pack private holdouts for v1-scale anti-gaming hardening; the
  rotation protocol is documented, but multiple active/shadow packs are not
  implemented
