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
- v0 release-gate audit script that reports `v0_ready: false` with explicit
  unmet gates while the repo is still alpha/pre-v0
- release evidence registry that keeps local validation, fresh-clone validation,
  remote CI, Docker smoke, privacy scan, release-note separation, and protected
  private-holdout execution false until a real v0 candidate satisfies them
- leaderboard submission validation with a tracked public harness-check example
  that is schema-valid, cross-checked against a source run summary, and not
  leaderboard eligible
- GitHub Actions workflow for public validation gates, including Docker runtime
  smoke
- scripted and model baseline summaries

## Verified Locally

The following checks have been run successfully on the current local scaffold:

```bash
python3 -Wd -m unittest discover -s tests
python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_v0_release.py --allow-incomplete
python3 scripts/validate_leaderboard_submission.py --submission 'examples/leaderboard/*.json' --require-source-summary
python3 -m compileall -q authzbench apps tests scripts
docker compose config
python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/scripted_baseline_agent.py' --results-dir results/scripted-baseline --timeout-seconds 10 --benchmark-commit-sha "$(git rev-parse HEAD)" --agent scripted_baseline_agent --model deterministic-script --harness-type scripted
python3 scripts/validate_public.py --include-scripted-baseline
```

The legacy Kiro baseline snapshots were run on the earlier 15-task split and
should be rerun before any tagged release. Docker runtime smoke requires a
Docker daemon and is covered by the GitHub Actions public-validation workflow.

## Baseline Results

| Baseline | Tasks | Passed | Exploit-proven success | False-positive rate | Authorized-allow pass |
| --- | ---: | ---: | ---: | ---: | ---: |
| Scripted sanity baseline | 44 | 44 | 1.0 | 0.0 | 1.0 |
| Live HTTP scripted baseline legacy snapshot | 15 | 15 | 1.0 | 0.0 | not tracked |
| Kiro `claude-sonnet-4.6` no-tools legacy snapshot | 15 | 11 | 0.3333 | 0.0 | not tracked |
| Kiro `qwen3-coder-next` no-tools legacy snapshot | 15 | 8 | 0.0 | 0.1111 | not tracked |

## Publication Readiness

Ready:

- public task manifests validate
- public docs explain task purpose, scoring, result artifacts, baselines, and limits
- tracked baseline summaries exist
- baseline registry exists and passes consistency validation while explicitly
  reporting `v0_baseline_ready: false`
- v0 release-gate audit exists and is run in public validation with
  `--allow-incomplete`, so alpha validation can pass while strict v0 readiness
  still fails honestly
- strict v0 readiness also depends on `docs/release-evidence.json`, which is
  intentionally unsatisfied for the current alpha/pre-v0 state
- leaderboard submission validator exists and is part of public validation
- tracked leaderboard examples are cross-checked against source run summaries
  instead of trusting hand-entered aggregate rows
- leaderboard-eligible rows require source summaries plus both vulnerable-task
  and secure-control coverage
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
- local-status paths and personal filesystem references have been removed from this document

Still required before the real v0 or a serious leaderboard:

- larger private holdout pack outside public Git history
- real non-public holdout tasks and protected execution; the local rehearsal
  generator is only a workflow test
- actual route-alias randomization and additional private-holdout decoy
  variation implemented in a real non-public holdout pack
- leaderboard-grade live-agent validation of per-task request-log correlation in
  addition to deterministic replay and CI smoke checks
- repeated model baselines on the current 44-task public split
- at least one current public tool-agent baseline
- decision on whether v0-candidate metrics become the default tagged-release
  scoring profile
- containerized or otherwise isolated model/agent execution for leaderboard runs
- remote CI status must stay explicit and passing before any real v0 tag
- `docs/release-evidence.json` must be updated with true evidence only after
  the corresponding checks pass for a real v0 release candidate
- repeated remote Docker runtime smoke on release-candidate commits
- post-push clone check from public `github.com` before tags or releases
