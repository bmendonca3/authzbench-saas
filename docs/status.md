# Release Status

Last updated: 2026-06-05

## Public Alpha Snapshot

AuthZBench-SaaS currently contains an alpha/pre-v0 public split:

- 6 Dockerized synthetic SaaS targets
- 44 public task manifests
- 18 vulnerable tasks
- 26 secure-control tasks
- 16 denial controls and 10 authorized-allow controls
- seeded runtime fixtures for tenant, object, organization, invoice, file, link,
  workspace, API-token, scope, and actor IDs
- route aliases and decoy controls across all six target apps
- target-side JSONL request logs for Docker HTTP targets
- alpha runner correlation into per-task `target-requests.jsonl` artifacts when
  `--target-log-dir` is supplied
- deterministic scorer with backend replay transcripts
- v0-candidate run-summary metrics for exploit proof, boundary reasoning,
  secure-control false reports, secure-control execution, and target-request
  coverage, plus invalid-submission tracking
- result and leaderboard schema documentation
- public holdout strategy documentation
- v0 task build matrix documentation
- baseline registry validation that separates harness checks, legacy snapshots,
  current public split summaries, and leaderboard eligibility
- current 44-task live HTTP scripted harness check against Docker targets, with
  target request-log correlation for the 18 vulnerable tasks
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

The following checks have been run successfully on the current local scaffold or
release-candidate checkpoint:

```bash
python3 -Wd -m unittest discover -s tests
python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_v0_release.py --allow-incomplete
python3 scripts/validate_v0_release.py
python3 scripts/validate_leaderboard_submission.py --submission 'examples/leaderboard/*.json' --require-source-summary
python3 -m compileall -q authzbench apps tests scripts
python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/scripted_baseline_agent.py' --results-dir results/scripted-baseline --timeout-seconds 10 --benchmark-commit-sha "$(git rev-parse HEAD)" --agent scripted_baseline_agent --model deterministic-script --harness-type scripted
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/validate_public.py --include-scripted-baseline --include-container-smoke
```

The legacy Kiro baseline snapshots were run on the earlier 15-task split and
are retained only as historical context. Docker runtime smoke requires a Docker
daemon; the `--include-container-smoke` path validates Docker Compose config,
starts the target stack, checks request logs, and is covered by the GitHub
Actions public-validation workflow.
The live HTTP scripted baseline has been rerun on the current 44-task public
split, but its target request-log coverage is 18/44 because the deterministic
agent only exercises vulnerable proof requests before submitting.

## Baseline Results

| Baseline | Tasks | Passed | Exploit-proven success | Boundary reasoning | False-positive rate | Authorized-allow pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Scripted sanity baseline | 44 | 44 | 1.0 | 1.0 | 0.0 | 1.0 |
| Live HTTP scripted baseline | 44 | 44 | 1.0 | 1.0 | 0.0 | 1.0 |
| Heuristic live HTTP prober | 44 | 33 | 0.6111 | 0.6667 | 0.0 | 1.0 |
| Kiro `claude-sonnet-4.6` no-tools legacy snapshot | 15 | 11 | 0.3333 | not tracked | 0.0 | not tracked |
| Kiro `qwen3-coder-next` no-tools legacy snapshot | 15 | 8 | 0.0 | not tracked | 0.1111 | not tracked |
| Kiro `claude-opus-4.6` no-tools current run 1 | 44 | 27 | 0.6667 | 0.0556 | 0.0 | 1.0 |
| Kiro `claude-opus-4.6` no-tools current run 2 | 44 | 27 | 0.6667 | 0.0556 | 0.0 | 1.0 |
| Kiro `claude-sonnet-4.6` no-tools current run 1 | 44 | 29 | 0.7778 | 0.1667 | 0.0 | 1.0 |
| Kiro `claude-sonnet-4.6` no-tools current run 2 | 44 | 29 | 0.7778 | 0.1667 | 0.0 | 1.0 |
| Kiro `claude-haiku-4.5` no-tools current run 1 | 44 | 26 | 0.2222 | 0.0 | 0.0 | 1.0 |
| Kiro `claude-haiku-4.5` no-tools current run 2 | 44 | 26 | 0.2222 | 0.0 | 0.0 | 1.0 |
| Kiro `deepseek-3.2` no-tools current run 1 | 44 | 26 | 0.0 | 0.0 | 0.0 | 1.0 |
| Kiro `deepseek-3.2` no-tools current run 2 | 44 | 26 | 0.0 | 0.0 | 0.0 | 1.0 |
| Kiro `qwen3-coder-next` no-tools current run 1 | 44 | 26 | 0.0 | 0.0 | 0.0 | 1.0 |
| Kiro `qwen3-coder-next` no-tools current run 2 | 44 | 25 | 0.0 | 0.0 | 0.0385 | 1.0 |

## Publication Readiness

Ready:

- public task manifests validate
- public docs explain task purpose, scoring, result artifacts, baselines, and limits
- tracked baseline summaries exist
- current live HTTP scripted harness summary exists for the 44-task public split
- baseline registry exists and passes consistency validation while reporting
  `v0_baseline_ready: true` for baseline evidence only
- a heuristic live HTTP prober now provides 44/44 target-request correlation
  across vulnerable and control public tasks, but it is classified as a harness
  check rather than a v0 tool-agent baseline
- five repeated current public model families exist: Kiro `claude-opus-4.6`,
  `claude-sonnet-4.6`, `claude-haiku-4.5`, `deepseek-3.2`, and
  `qwen3-coder-next` no-tools, each with two distinct 44-task run summaries
- a current public Kiro live HTTP tool-agent baseline exists with 44/44
  target-request correlation plus per-task model-tool plans and tool-probe
  artifacts
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
- one redacted release-candidate private-holdout leaderboard row exists under
  `leaderboard_submissions/`, backed by a tracked aggregate source summary and
  validated without publishing private task bodies, IDs, seeds, refs, routes, or
  raw result bundles
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
- two redacted protected-private execution summaries validate as repeated
  aggregate evidence without publishing private task rows or raw result bundles
- final holdout anti-gaming and final release-readiness review summaries exist
  and mark all required review-registry sections v0-candidate ready
- local-status paths and personal filesystem references have been removed from this document

Still required before a tagged release or hosted public leaderboard:

- remote CI status must stay explicit and passing before any real v0 tag
- keep `docs/release-evidence.json` tied to exact command, commit, CI, and
  artifact evidence as later release checks are rerun
- post-push clone check from public `github.com` before tags or releases
- hosted or fully containerized leaderboard execution if third-party submissions
  will be accepted at scale
- rotating multi-pack private holdouts for v1-scale anti-gaming hardening
