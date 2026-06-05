# Release Status

Last updated: 2026-06-05

## Public Alpha Snapshot

AuthZBench-SaaS currently contains an alpha/pre-v0 public split:

- 3 Dockerized synthetic SaaS targets
- 21 public task manifests
- 9 vulnerable tasks
- 12 secure-control tasks
- seeded runtime fixtures for tenant, object, organization, invoice, and actor IDs
- prototype route alias and decoy endpoint coverage
- target-side JSONL request logs for Docker HTTP targets
- alpha runner correlation into per-task `target-requests.jsonl` artifacts when
  `--target-log-dir` is supplied
- deterministic scorer with backend replay transcripts
- result and leaderboard schema documentation
- public holdout strategy documentation
- scripted and model baseline summaries

## Verified Locally

The following checks have been run successfully on the current local scaffold:

```bash
python3 -Wd -m unittest discover -s tests
python3 -m authzbench.validate_manifests --task 'tasks/*/*.json'
python3 -m compileall -q authzbench apps tests scripts
docker compose config
python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/scripted_baseline_agent.py' --results-dir results/scripted-baseline --timeout-seconds 10 --benchmark-commit-sha "$(git rev-parse HEAD)" --agent scripted_baseline_agent --model deterministic-script --harness-type scripted
python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/kiro_baseline_agent.py --model claude-sonnet-4.6 --timeout-seconds 90' --results-dir results/kiro-sonnet-full --timeout-seconds 120 --benchmark-commit-sha "$(git rev-parse HEAD)" --agent kiro_baseline_agent --model claude-sonnet-4.6 --harness-type no-tools-model
python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/kiro_baseline_agent.py --model qwen3-coder-next --timeout-seconds 90' --results-dir results/kiro-qwen-full --timeout-seconds 120 --benchmark-commit-sha "$(git rev-parse HEAD)" --agent kiro_baseline_agent --model qwen3-coder-next --harness-type no-tools-model
docker compose up --build -d
python3 scripts/container_smoke.py
docker compose down
```

The Kiro baseline commands exit nonzero when the model misses any benchmark
task. Their generated `summary.json` files are still valid baseline evidence.

## Baseline Results

| Baseline | Tasks | Passed | Exploit-proven success | False-positive rate |
| --- | ---: | ---: | ---: | ---: |
| Scripted sanity baseline | 21 | 21 | 1.0 | 0.0 |
| Live HTTP scripted baseline legacy snapshot | 15 | 15 | 1.0 | 0.0 |
| Kiro `claude-sonnet-4.6` no-tools legacy snapshot | 15 | 11 | 0.3333 | 0.0 |
| Kiro `qwen3-coder-next` no-tools legacy snapshot | 15 | 8 | 0.0 | 0.1111 |

## Publication Readiness

Ready:

- public task manifests validate
- public docs explain task purpose, scoring, result artifacts, baselines, and limits
- tracked baseline summaries exist
- private holdout JSON is excluded from the publishable repo
- local-status paths and personal filesystem references have been removed from this document

Still required before the real v0 or a serious leaderboard:

- expansion beyond the current 3-app/21-task alpha split
- larger private holdout pack outside public Git history
- route alias expansion and randomization
- Docker-backed validation of per-task request-log correlation in addition to
  deterministic replay
- containerized or otherwise isolated model/agent execution for leaderboard runs
- final secret/personal-info scan immediately before push
- post-push clone check from public `github.com`
