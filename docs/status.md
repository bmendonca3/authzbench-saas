# Release Status

Last updated: 2026-06-05

## Public v0 Snapshot

AuthZBench-SaaS v0 currently contains:

- 2 Dockerized synthetic SaaS targets
- 12 public task manifests
- 5 vulnerable tasks
- 7 secure-control tasks
- seeded runtime fixtures for tenant, object, organization, invoice, and actor IDs
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
python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/scripted_baseline_agent.py' --results-dir results/scripted-baseline --timeout-seconds 10
python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/kiro_baseline_agent.py --model claude-sonnet-4.6 --timeout-seconds 90' --results-dir results/kiro-sonnet-full --timeout-seconds 120
python3 -m authzbench.run --task 'tasks/*/*.json' --agent-cmd 'python3 scripts/kiro_baseline_agent.py --model qwen3-coder-next --timeout-seconds 90' --results-dir results/kiro-qwen-full --timeout-seconds 120
```

The Kiro baseline commands exit nonzero when the model misses any benchmark
task. Their generated `summary.json` files are still valid baseline evidence.

## Baseline Results

| Baseline | Tasks | Passed | Exploit-proven success | False-positive rate |
| --- | ---: | ---: | ---: | ---: |
| Scripted sanity baseline | 12 | 12 | 1.0 | 0.0 |
| Kiro `claude-sonnet-4.6` no-tools | 12 | 10 | 0.6 | 0.0 |
| Kiro `qwen3-coder-next` no-tools | 12 | 7 | 0.0 | 0.0 |

## Publication Readiness

Ready:

- public task manifests validate
- public docs explain task purpose, scoring, result artifacts, baselines, and limits
- tracked baseline summaries exist
- private holdout JSON is excluded from the publishable repo
- local-status paths and personal filesystem references have been removed from this document

Still required before a serious leaderboard:

- larger private holdout pack outside public Git history
- route alias randomization
- containerized or otherwise isolated model/agent execution for leaderboard runs
- Docker container smoke on a machine with Docker available
- final secret/personal-info scan immediately before push
- post-push clone check from public `github.com`
