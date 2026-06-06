# Release Status

Last updated: 2026-06-06

## Public v0.0 Snapshot

AuthZBench-SaaS currently contains a released v0.0 public split:

- 6 Dockerized synthetic SaaS targets
- 46 public task manifests
- 19 vulnerable tasks
- 27 secure-control tasks
- 16 denial controls and 11 authorized-allow controls
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
  current public split summaries, and leaderboard eligibility
- current 46-task deterministic scripted harness check
- repeated current 46-task no-tools Kiro `qwen3-coder-next` model baseline
- repeated current 46-task no-tools Kiro `claude-haiku-4.5` model baseline
- repeated current 46-task no-tools Kiro `claude-sonnet-4.6` model baseline
- repeated current 46-task no-tools Kiro `glm-5` model baseline
- repeated current 46-task live HTTP Kiro `claude-sonnet-4.6` tool-agent baseline with
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
- scripted and model baseline summaries

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

The baseline credibility gate now has five repeated current model/agent
families. Strict `python3 scripts/validate_v0_release.py` should be rerun in a
maintainer checkout before future tags because release evidence and CI
references are time-sensitive.

The legacy Kiro baseline snapshots were run on the earlier 15-task split and
are retained only as historical context. Docker runtime smoke requires a Docker
daemon; the `--include-container-smoke` path validates Docker Compose config,
starts the target stack, checks request logs, and is covered by the GitHub
Actions public-validation workflow.
The deterministic scripted baseline has been rerun on the current 46-task
public split. The `qwen3-coder-next` no-tools Kiro baseline has also been
rerun twice on the current 46-task split. The `claude-haiku-4.5` no-tools Kiro
baseline has also been rerun twice on the 46-task split; the two runs span
adjacent commits where only chart rendering/status text changed. The
`claude-sonnet-4.6` no-tools Kiro baseline has also been rerun twice on the
46-task split. The `glm-5` no-tools Kiro baseline has also been rerun twice on
the 46-task split. The older live
HTTP scripted, heuristic, and older Kiro model/tool-agent summaries are now
stale 44-task snapshots because the public split changed. The current
`claude-sonnet-4.6` live HTTP tool-agent baseline now has two 46-task
public-split runs with per-task plan/probe artifacts and full target-request
correlation in both runs, but it is still not private-holdout or hosted
leaderboard evidence.
The second Qwen run also had one invalid submission on a vulnerable task
(`invalid_submission_rate: 0.0217`), so the current Qwen evidence should be read
as repeatability evidence, not a polished model ranking.

## Baseline Results

| Baseline | Tasks | Passed | Exploit-proven success | Boundary reasoning | False-positive rate | Authorized-allow pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Scripted sanity baseline, current | 46 | 46 | 1.0 | 1.0 | 0.0 | 1.0 |
| Kiro `qwen3-coder-next` no-tools current run 1 | 46 | 27 | 0.0 | 0.0 | 0.0 | 1.0 |
| Kiro `qwen3-coder-next` no-tools current run 2 | 46 | 27 | 0.0526 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-haiku-4.5` no-tools current run 1 | 46 | 26 | 0.2632 | 0.0 | 0.037 | 1.0 |
| Kiro `claude-haiku-4.5` no-tools current run 2 | 46 | 27 | 0.0526 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-sonnet-4.6` no-tools current run 1 | 46 | 27 | 0.6316 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-sonnet-4.6` no-tools current run 2 | 46 | 26 | 0.4211 | 0.0 | 0.037 | 1.0 |
| Kiro `glm-5` no-tools current run 1 | 46 | 27 | 0.2105 | 0.0 | 0.0 | 1.0 |
| Kiro `glm-5` no-tools current run 2 | 46 | 27 | 0.0526 | 0.0 | 0.0 | 1.0 |
| Kiro live HTTP tool-agent `claude-sonnet-4.6` current run 1 | 46 | 27 | 0.7368 | 0.0 | 0.0 | 1.0 |
| Kiro live HTTP tool-agent `claude-sonnet-4.6` current run 2 | 46 | 27 | 0.7368 | 0.0 | 0.0 | 1.0 |
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

The current Qwen repeat is useful because it shows variance, not because it is
a strong model result. Run 2 found one replay-proven vulnerable task but still
had `boundary_reasoning_pass_rate: 0.0` and one invalid vulnerable-task
submission; `v0_mean_score` remains a full-pass aggregate, separate from
partial-credit `mean_score`.
The current Haiku repeat adds a second current public no-tools model family. It
showed some exploit-proof success but still produced no fully passed vulnerable
tasks because vulnerable boundary reasoning remained `0.0`; run 1 also had one
secure-control false report.
The current Sonnet no-tools repeat adds a third current public no-tools model
family. It proved stronger vulnerable replay evidence than Qwen or Haiku in
these public runs, but still produced no fully passed vulnerable tasks because
vulnerable boundary reasoning remained `0.0`; run 2 also had one secure-control
false report.
The current GLM repeat adds a fourth current public no-tools model family and
the fifth repeated current model/agent family overall when counted with the
tool-agent family. It produced 1-4 exploit-proven vulnerable replays per run,
zero fully passed vulnerable tasks, and zero secure-control false reports.

## Publication Readiness

Ready public v0.0 infrastructure:

This list is not a hosted-leaderboard claim. The baseline
credibility sub-gate now has five repeated current-public model/agent-family
baselines after the 46-task split change.

- public task manifests validate
- public docs explain task purpose, scoring, result artifacts, baselines, and limits
- tracked baseline summaries exist
- current deterministic scripted harness summary exists for the 46-task public split
- four repeated current no-tools model-family baselines and one repeated current
  live HTTP tool-agent family exist on the 46-task public split
- one repeated current live HTTP tool-agent baseline exists on the 46-task
  public split, with plan/probe artifacts and full target-request correlation
- baseline registry exists and passes consistency validation while reporting
  `v0_baseline_ready: true`
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
- hosted or fully containerized leaderboard execution if third-party submissions
  will be accepted at scale
- rotating multi-pack private holdouts for v1-scale anti-gaming hardening
