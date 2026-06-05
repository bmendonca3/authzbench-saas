# AuthZBench-SaaS

![AuthZBench-SaaS alpha/pre-v0 overview](assets/authzbench-saas-alpha-pre-v0.png)

AuthZBench-SaaS is an **alpha / pre-v0 benchmark scaffold** for testing whether
AI agents can find SaaS authorization bugs without hallucinating reports on
secure controls.

It focuses on the messy parts of real SaaS security work: tenants, roles,
object ownership, API tokens, backend replay evidence, request logs, and false
positive discipline.

This is not leaderboard-ready yet. The public repo is useful for inspection,
local testing, and early baseline comparison. The real v0 bar is stricter.

## What Is Included

- 6 synthetic SaaS apps
- 44 public benchmark tasks
- 18 vulnerable tasks
- 26 secure-control tasks
- 10 authorized-allow controls
- deterministic backend replay scoring
- target-side request logging for Docker runs
- public baseline summaries for scripted and model runs
- CI, fresh-clone validation, release-gate auditing, and privacy checks

All apps are intentionally vulnerable local fixtures. Do not expose them to the
public internet.

## Target Apps

| App | Port | Focus |
| --- | ---: | --- |
| `project_mgmt` | `8011` | cross-tenant project/task access |
| `billing` | `8012` | billing plan and invoice authorization |
| `support` | `8013` | ticket access, status changes, invite abuse |
| `file_sharing` | `8014` | files, share links, stale-link access |
| `api_tokens` | `8015` | token tenant binding and scope checks |
| `audit_settings` | `8016` | audit logs, exports, admin settings |

## Quick Start

Render a task:

```bash
python3 -m authzbench.render_task tasks/project_mgmt/pm_bola_read_alpha_from_beta.json
```

Score an example submission:

```bash
python3 -m authzbench.score \
  tasks/project_mgmt/pm_bola_read_alpha_from_beta.json \
  examples/submissions/pm_bola_read_alpha_from_beta.valid.json
```

Run public validation:

```bash
python3 scripts/validate_public.py --include-scripted-baseline
```

Run the Docker smoke gate when Docker is available:

```bash
python3 scripts/validate_public.py \
  --include-scripted-baseline \
  --include-container-smoke
```

Audit the real v0 gates:

```bash
python3 scripts/validate_v0_release.py --allow-incomplete
```

That command should currently report `v0_ready: false`.

## Running Targets

```bash
docker compose up --build -d
python3 scripts/container_smoke.py
docker compose down
```

Docker request logs are written to `captures/request-logs/`, which is ignored by
Git.

## Running a Baseline

Deterministic scripted baseline:

```bash
python3 -m authzbench.run \
  --task 'tasks/*/*.json' \
  --agent-cmd 'python3 scripts/scripted_baseline_agent.py' \
  --results-dir results/scripted-baseline \
  --timeout-seconds 10 \
  --benchmark-commit-sha "$(git rev-parse HEAD)" \
  --agent scripted_baseline_agent \
  --model deterministic-script \
  --harness-type scripted
```

No-tools Kiro model baseline:

```bash
python3 -m authzbench.run \
  --task 'tasks/*/*.json' \
  --agent-cmd 'python3 scripts/kiro_baseline_agent.py --model claude-sonnet-4.6 --timeout-seconds 60' \
  --results-dir results/kiro-sonnet-current-public \
  --timeout-seconds 75 \
  --benchmark-commit-sha "$(git rev-parse HEAD)" \
  --agent kiro_baseline_agent \
  --model claude-sonnet-4.6 \
  --harness-type no-tools-model
```

Result bundles under `results/` are local artifacts and are ignored by Git.

## Current Baseline Evidence

The baseline registry lives at
[`baselines/baseline-registry.json`](baselines/baseline-registry.json).

| Baseline | Public tasks | Passed | Exploit-proven rate | False-positive rate |
| --- | ---: | ---: | ---: | ---: |
| Scripted sanity baseline | 44 | 44 | 1.0 | 0.0 |
| Live HTTP scripted baseline | 44 | 44 | 1.0 | 0.0 |
| Kiro `claude-sonnet-4.6` current run 1 | 44 | 29 | 0.7778 | 0.0 |
| Kiro `claude-sonnet-4.6` current run 2 | 44 | 29 | 0.7778 | 0.0 |
| Kiro `deepseek-3.2` current run 1 | 44 | 26 | 0.0 | 0.0 |
| Kiro `deepseek-3.2` current run 2 | 44 | 26 | 0.0 | 0.0 |
| Kiro `qwen3-coder-next` current run 1 | 44 | 26 | 0.0 | 0.0 |
| Kiro `qwen3-coder-next` current run 2 | 44 | 25 | 0.0 | 0.0385 |

The scripted baselines are harness checks, not model results. The model runs are
public-split evidence only; they are not private-holdout or leaderboard results.

Current registry status:

- 3 of 5 required repeated model/agent families
- no accepted tool-agent baseline yet
- `v0_baseline_ready: false`

## Scoring Summary

AuthZBench-SaaS scores agents on:

- replayable exploit proof for vulnerable tasks
- correct actor, tenant, role, object, or token boundary reasoning
- false-positive avoidance on secure controls
- authorized-allow behavior where access should succeed
- target-request correlation when live Docker targets are used
- invalid or malformed submissions

See [`docs/methodology.md`](docs/methodology.md) and
[`docs/result-schema.md`](docs/result-schema.md) for the full schema.

## Private Holdouts

Private holdout manifests are not included in the public repo. The ignored
`tasks_private/holdout/` path is reserved for maintainers to keep unpublished
tasks, hidden seeds, private routes, vulnerability locations, and scorer oracles.

See [`docs/holdout-and-contamination.md`](docs/holdout-and-contamination.md).

## What Is Still Missing for v0

AuthZBench-SaaS should not be called v0, leaderboard-ready, or a validated model
benchmark until the strict release gate passes.

Remaining major gaps:

- two more repeated current model/agent families
- one real live HTTP tool-agent baseline
- artifact-backed leaderboard submissions
- stronger live-target proof across vulnerable and control tasks
- release evidence fields with supporting commands, commits, CI links, and
  privacy checks
- final sectional panel review

Run:

```bash
python3 scripts/validate_v0_release.py
```

Strict mode should fail until those gaps are closed.

## Documentation

- [`docs/goal.md`](docs/goal.md): v0 definition
- [`ROADMAP.md`](ROADMAP.md): path from alpha to v0
- [`docs/v0-release-plan.md`](docs/v0-release-plan.md): release criteria
- [`docs/benchmark-card.md`](docs/benchmark-card.md): intended use and limits
- [`docs/baseline-credibility.md`](docs/baseline-credibility.md): baseline bar
- [`docs/leaderboard-schema.md`](docs/leaderboard-schema.md): leaderboard format
- [`docs/publish-checklist.md`](docs/publish-checklist.md): publication checks
- [`SECURITY.md`](SECURITY.md): safe handling guidance

## License

MIT. See [`LICENSE`](LICENSE).
