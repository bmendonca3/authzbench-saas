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
- result and leaderboard schema documentation
- public holdout strategy documentation
- v0 task build matrix documentation
- scripted and model baseline summaries

## Verified Locally

The following checks have been run successfully on the current local scaffold:

```bash
python3 -Wd -m unittest discover -s tests
python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'
python3 -m compileall -q authzbench apps tests scripts
docker compose config
python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/scripted_baseline_agent.py' --results-dir results/scripted-baseline --timeout-seconds 10 --benchmark-commit-sha "$(git rev-parse HEAD)" --agent scripted_baseline_agent --model deterministic-script --harness-type scripted
python3 scripts/validate_public.py --include-scripted-baseline
```

The legacy Kiro baseline snapshots were run on the earlier 15-task split and
should be rerun before any tagged release. Docker runtime smoke also requires a
local Docker daemon; Docker Compose config validation is covered by the public
validation script.

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
- reproducible fresh-clone validation script exists
- private holdout pack validator exists for ignored local holdouts, including
  app coverage, control subtype mix, and public ID/seed overlap checks
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
- route-alias randomization and additional private-holdout decoy variation
- Docker-backed validation of per-task request-log correlation in addition to
  deterministic replay
- containerized or otherwise isolated model/agent execution for leaderboard runs
- CI workflow for public validation gates
- Docker-backed runtime smoke when a daemon is available
- post-push clone check from public `github.com` before tags or releases
