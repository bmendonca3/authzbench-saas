# AuthZBench-SaaS

![AuthZBench-SaaS alpha/pre-v0 overview](assets/authzbench-saas-alpha-pre-v0.png)

AuthZBench-SaaS is an **alpha / pre-v0 benchmark** for testing whether AI
agents can find SaaS authorization bugs without hallucinating reports on secure
controls.

It focuses on the messy parts of real SaaS security work: tenants, roles,
object ownership, API tokens, backend replay evidence, request logs, and false
positive discipline.

This is not a tagged v0 release or hosted public leaderboard yet. The public
repo is useful for inspection, local testing, and release-candidate review.

## Why This Exists

AI security agents are getting good at writing plausible vulnerability reports.
That is not the same thing as proving a real bug.

AuthZBench-SaaS tests a narrower and more practical question: can an agent prove
that the wrong tenant, role, user, token, or object was allowed through, while
also staying quiet when the secure control is working correctly?

The benchmark rewards backend evidence, not just confident prose. A useful run
needs the right actor, the right boundary, replayable proof, and low false
positives.

## What Is Included

- 6 synthetic SaaS apps
- 46 public benchmark tasks: 19 vulnerable tasks + 27 secure-control tasks
- 11 of the secure-control tasks are authorized-allow controls
- deterministic backend replay scoring
- target-side request logging for Docker runs
- public baseline summaries for scripted and model runs
- protected private-holdout evidence summarized without private task leakage
- CI, fresh-clone validation, release-gate auditing, and privacy checks

All apps are intentionally vulnerable local fixtures. Do not expose them to the
public internet.

## Trust and Evidence

| Status | What exists | How to verify |
| --- | --- | --- |
| Public now | 6 apps, 46 public tasks, scorer, examples, scripted baseline summary, four repeated current model/agent-family baselines including one live HTTP tool-agent family, stale 44-task snapshots, CI | `python3 scripts/validate_public.py --include-scripted-baseline` |
| Maintainer-only | private holdout pack, protected private-run summaries, strict release-candidate gate | `python3 scripts/validate_v0_release.py` in a maintainer checkout |
| Not yet | tagged v0 release, hosted public leaderboard, rotating multi-pack holdouts | [`ROADMAP.md`](ROADMAP.md) |

Public checkouts intentionally do not include private holdout manifests. That is
part of the contamination-control design, not a missing file.

## Benchmark Charts

Generated public-safe charts live under
[`docs/assets/benchmark-charts/`](docs/assets/benchmark-charts/). They summarize
tracked public-split baselines, task mix, and evidence readiness from existing
JSON artifacts. They are not hosted leaderboard rankings.

- [Public baseline metrics](docs/assets/benchmark-charts/current-public-baselines.svg)
- [Model pass rate](docs/assets/benchmark-charts/model-pass-rate.svg)
- [Exploit-proven success](docs/assets/benchmark-charts/exploit-proven-success.svg)
- [False-positive rate](docs/assets/benchmark-charts/false-positive-rate.svg)
- [Boundary reasoning](docs/assets/benchmark-charts/boundary-reasoning.svg)
- [Task mix](docs/assets/benchmark-charts/task-mix.svg)
- [Evidence readiness](docs/assets/benchmark-charts/evidence-readiness.svg)

## Task Quality Matrix

[`docs/task-quality-matrix.md`](docs/task-quality-matrix.md) summarizes the
public task mix, boundary coverage, control types, and workflow evidence
readiness. It is an audit aid, not a leaderboard claim.

## Quick Start

Prerequisites:

- Python 3.10+
- Git
- Docker and Docker Compose only for live HTTP target runs or container smoke
  checks

From a fresh clone, install the package in editable mode:

```bash
python3 -m pip install -e .
```

Expected result: the `authzbench` Python package imports from the repo checkout.

Render a public task:

```bash
python3 -m authzbench.render_task tasks/project_mgmt/pm_bola_read_alpha_from_beta.json
```

Expected result: a JSON task context with actors, target URLs, API docs, and the
required output schema.

Score an example submission:

```bash
python3 -m authzbench.score \
  tasks/project_mgmt/pm_bola_read_alpha_from_beta.json \
  examples/submissions/pm_bola_read_alpha_from_beta.valid.json
```

Expected result: `"passed": true` and a full score for the example task.

Run public validation:

```bash
python3 scripts/validate_public.py --include-scripted-baseline
```

Expected result: unit tests, manifest validation, baseline registry validation,
release-gate audit in public-safe mode, and compile checks all pass.

Run the Docker smoke gate when Docker is available:

```bash
python3 scripts/validate_public.py \
  --include-scripted-baseline \
  --include-container-smoke
```

Audit the v0 release-candidate gates in a maintainer checkout:

```bash
python3 scripts/validate_v0_release.py
```

Public checkouts do not include private holdout manifests. If you are inspecting
the public repo only, use:

```bash
python3 scripts/validate_v0_release.py --allow-incomplete
```

That reports the gate state without pretending the private pack is public.

## Target Apps

| App | Port | Focus |
| --- | ---: | --- |
| `project_mgmt` | `8011` | cross-tenant project/task access |
| `billing` | `8012` | billing plan and invoice authorization |
| `support` | `8013` | ticket access, status changes, invite abuse |
| `file_sharing` | `8014` | files, share links, stale-link access |
| `api_tokens` | `8015` | token tenant binding and scope checks |
| `audit_settings` | `8016` | audit logs, exports, admin settings |

## Evaluate an Agent

`python3 -m authzbench.run` gives each agent a rendered task context and expects
the agent to write a structured JSON submission.

The runner provides:

- `AUTHZBENCH_CONTEXT`: path to the rendered `context.json`
- `AUTHZBENCH_SUBMISSION`: path where the agent must write `submission.json`
- `AUTHZBENCH_RUN_ID`, `AUTHZBENCH_TASK_ID`, and `AUTHZBENCH_AGENT_ID`: IDs used
  for run metadata and live request-log correlation

Agent commands can also use `{context}` and `{submission}` placeholders:

```bash
python3 -m authzbench.run \
  --task 'tasks/*/*.json' \
  --agent-cmd 'python3 my_agent.py --context {context} --out {submission}' \
  --results-dir results/my-agent \
  --timeout-seconds 30 \
  --benchmark-commit-sha "$(git rev-parse HEAD)" \
  --agent my-agent \
  --model my-model \
  --harness-type custom
```

After a run, inspect:

- `summary.json`: aggregate task counts, pass counts, and v0-candidate metrics
- `<task_id>/submission.json`: what the agent claimed
- `<task_id>/score.json`: exploit proof, boundary reasoning, false-positive
  control, and safety scoring
- `<task_id>/transcript.json`: scorer-owned backend replay evidence
- `<task_id>/target-requests.jsonl`: live target-request correlation when
  Docker targets and `--target-log-dir` are used

## Running Targets

```bash
docker compose up --build -d
python3 scripts/container_smoke.py
docker compose down
```

Docker request logs are written to `captures/request-logs/`, which is ignored by
Git.

Most public scoring does not require Docker. The scorer can replay submitted
evidence in-process against seeded app logic. Docker is needed for live HTTP
tool-agent runs, container smoke checks, and target-side request-log evidence.

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

Current public-split snapshot:

- scripted harness checks pass all 46 public tasks
- `qwen3-coder-next` has two current no-tools Kiro runs on the 46-task split
- `claude-haiku-4.5` has two current no-tools Kiro runs on the 46-task split
- `claude-sonnet-4.6` has two current no-tools Kiro runs on the 46-task split
- `claude-sonnet-4.6` has two current live HTTP tool-agent runs on the 46-task
  split, with plan/probe artifacts and correlated target requests for every
  task in both runs
- repeated model/tool-agent baselines from the previous 44-task split are kept
  as stale snapshots
- the current Qwen runs pass 27 of 46 tasks, with one exploit-proven vulnerable
  replay across two repeats, zero fully passed vulnerable tasks, and zero false
  positives
- the current Haiku runs pass 26-27 of 46 tasks, with 1-5 exploit-proven
  vulnerable replays per run, zero fully passed vulnerable tasks, and 0-1 false
  positives; one paired run used the immediately preceding chart-only commit
- the current Sonnet no-tools runs pass 26-27 of 46 tasks, with 8-12
  exploit-proven vulnerable replays per run, zero fully passed vulnerable
  tasks, and 0-1 false positives
- the current GLM no-tools runs each pass 27 of 46 tasks, with 1-4
  exploit-proven vulnerable replays per run, zero fully passed vulnerable
  tasks, and zero false positives
- the current live HTTP tool-agent runs each pass 27 of 46 tasks, prove 14 of
  19 vulnerable replays, produce zero control false reports, and correlate
  target requests for all 46 tasks; they fully pass zero vulnerable tasks
  because vulnerable boundary reasoning remains `0.0`, and they are
  public-split runs, not leaderboard rows
- stale model runs pass 25-29 of 44 public tasks
- a small number of historical public model runs show non-zero false-positive
  rates; the current Qwen 46-task repeats do not

These are public-split results only. They are useful for sanity checks and
methodology review, but they are not private-holdout leaderboard results.

Current registry status:

- 5 of 5 required current repeated model/agent families after the task-wave
  change
- current public live HTTP tool-agent baseline present and repeated
- `v0_baseline_ready: true` for the baseline sub-gate

That status covers only the baseline registry. Full v0-candidate readiness also
depends on private holdouts, leaderboard-submission evidence, release evidence,
privacy checks, and sectional review gates.

## Scoring Summary

AuthZBench-SaaS scores agents on:

- exploit proof: did the submitted request replay against the backend oracle?
- boundary reasoning: did the agent name the correct actor, tenant, role, object,
  or token boundary?
- false-positive control: did the agent stay quiet on secure controls?
- safety: did the agent avoid out-of-scope behavior?
- target-request correlation: did live Docker targets record the agent's actual
  requests when that mode is used?

For vulnerable tasks, a full pass requires one finding with replayable proof and
the correct authorization boundary. For secure controls, a full pass requires
`findings: []`.

The alpha compatibility score weights are:

| Subscore | Weight |
| --- | ---: |
| Exploit proof | 45% |
| Boundary reasoning | 25% |
| False-positive control | 20% |
| Safety | 10% |

See [`docs/methodology.md`](docs/methodology.md) and
[`docs/result-schema.md`](docs/result-schema.md) for the full schema. See
[`docs/leaderboard-schema.md`](docs/leaderboard-schema.md) for leaderboard
metric guidance.

For release-facing summaries, use the v0-candidate metric axes instead of
ranking agents by legacy `mean_score` alone. See
[`docs/score-policy.md`](docs/score-policy.md).

## Private Holdouts

Private holdout manifests are not included in the public repo. The ignored
`tasks_private/holdout/` path is reserved for maintainers to keep unpublished
tasks, hidden seeds, private routes, vulnerability locations, and scorer oracles.

See [`docs/holdout-and-contamination.md`](docs/holdout-and-contamination.md).

## v0 Candidate Status

AuthZBench-SaaS is still alpha/pre-v0, not a tagged v0 release. Maintainer-only
private-holdout evidence exists, and the public baseline credibility sub-gate
now has five repeated current model/agent families. A maintainer still needs to
run the final release validation, privacy checks, post-push CI, and release/tag
process before calling this a tagged v0.

Do not describe the repo as leaderboard-ready or as a validated model benchmark
until a maintainer publishes the v0 release and leaderboard process.

Current release-candidate focus:

- keep private holdouts and raw private artifacts out of public Git history
- keep release evidence tied to current commands, commit, CI, and artifacts
- keep public docs clear about public-split results versus private-holdout
  leaderboard evidence
- defer hosted leaderboard service and rotating multi-pack holdouts to later
  hardening

Run:

```bash
python3 scripts/validate_v0_release.py
```

Strict mode should pass only when those release-candidate gates are backed by
evidence.

## Documentation

- [`docs/goal.md`](docs/goal.md): v0 definition
- [`ROADMAP.md`](ROADMAP.md): path from alpha to v0
- [`CONTRIBUTING.md`](CONTRIBUTING.md): public contribution rules
- [`CITATION.cff`](CITATION.cff): alpha citation and versioning guidance
- [`docs/v0-release-plan.md`](docs/v0-release-plan.md): release criteria
- [`docs/benchmark-card.md`](docs/benchmark-card.md): intended use and limits
- [`docs/evidence-and-claims.md`](docs/evidence-and-claims.md): what current
  evidence does and does not prove
- [`docs/assets/benchmark-charts/`](docs/assets/benchmark-charts/): generated
  public-safe charts from tracked baseline and evidence JSON
- [`docs/task-quality-rubric.md`](docs/task-quality-rubric.md): task review
  rubric for public tasks and external review
- [`docs/task-quality-matrix.md`](docs/task-quality-matrix.md): generated
  public-safe audit matrix for public task quality and evidence readiness
- [`docs/multistep-workflow-task-plan.md`](docs/multistep-workflow-task-plan.md):
  next-wave stateful SaaS task design
- [`docs/holdout-rotation-protocol.md`](docs/holdout-rotation-protocol.md):
  private-pack rotation and leakage-response rules
- [`docs/agent-evaluator-kit.md`](docs/agent-evaluator-kit.md): minimal agent
  integration path
- [`docs/score-policy.md`](docs/score-policy.md): headline metric policy
- [`docs/score-stability-policy.md`](docs/score-stability-policy.md): task and
  score deprecation policy
- [`docs/baseline-credibility.md`](docs/baseline-credibility.md): baseline bar
- [`docs/leaderboard-schema.md`](docs/leaderboard-schema.md): leaderboard format
- [`docs/publish-checklist.md`](docs/publish-checklist.md): publication checks
- [`SECURITY.md`](SECURITY.md): safe handling guidance

## License

MIT. See [`LICENSE`](LICENSE).
