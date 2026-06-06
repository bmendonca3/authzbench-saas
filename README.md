# AuthZBench-SaaS

![AuthZBench-SaaS alpha/pre-v0 overview](assets/authzbench-saas-alpha-pre-v0.png)

AuthZBench-SaaS is a SaaS authorization benchmark for testing whether AI agents
can prove access-control failures with backend evidence while avoiding false
reports on secure controls.

The benchmark focuses on a narrow, practical security question:

> Can an agent show that the wrong tenant, role, user, token, or object was
> allowed through, and can it stay quiet when access is correctly denied or
> correctly allowed?

This repository is a **released v0.0 benchmark artifact**. The strict maintainer
gate has evidence, and the `v0.0` tag is public, but the project is not a hosted
leaderboard and should not be called a community benchmark yet.

## Why This Matters

AI security tools can produce convincing vulnerability reports without proving a
real vulnerability. Authorization bugs are a useful stress test because a correct
answer needs more than fluent prose:

- the right actor
- the right tenant, organization, project, object, role, or token boundary
- a replayable backend request
- no finding on secure-control tasks
- no unsafe or out-of-scope behavior

AuthZBench-SaaS rewards proof and penalizes unsupported claims.

## Current Snapshot

| Area | Current state |
| --- | --- |
| Public apps | 6 synthetic SaaS targets |
| Public tasks | 46 total: 19 vulnerable, 27 secure controls |
| Control mix | 16 denial controls, 11 authorized-allow controls |
| Baselines | 5 repeated current model/agent families, including one live HTTP tool-agent family |
| Scoring | Deterministic backend replay plus v0 evidence metrics |
| Private holdouts | Maintainer-only, ignored from public Git history |
| Release status | v0.0 released; hosted leaderboard and v1/community claims remain future work |
| Not included | Hosted leaderboard, rotating multi-pack holdouts, v1/community claims |

Public checkouts intentionally do not include private holdout manifests. That is
part of the contamination-control design, not a missing file.

## What Is Included

- 6 local SaaS fixtures: project management, billing, support, file sharing,
  API tokens, and audit settings
- 46 public task manifests with seeded tenants, users, roles, objects, tokens,
  scopes, routes, and controls
- deterministic scorer-owned backend replay
- Docker targets with request-log correlation for live HTTP agents
- repeated public baseline summaries for Kiro no-tools model runs and one Kiro
  live HTTP tool-agent family
- protected private-holdout summaries published only as redacted aggregate
  evidence
- leaderboard-submission schema, source-summary validation, benchmark
  fingerprints, and comparability keys
- public-safe benchmark charts, task-quality matrix, benchmark card, release
  gates, privacy checks, and fresh-clone validation

All apps are intentionally vulnerable local fixtures. Do not expose them to the
public internet.

## Evidence Boundaries

Supported claims:

- AuthZBench-SaaS is a released v0.0 artifact for SaaS authorization-agent
  evaluation.
- The current public split has repeated baseline evidence across 5 current
  model/agent families.
- The scorer can verify backend-replayable evidence and false-positive behavior.
- Maintainer-only private-holdout evidence exists without publishing private
  task bodies, routes, seeds, or oracles.

Unsupported claims:

- hosted leaderboard readiness
- v1/community-benchmark maturity
- production vulnerability discovery
- private model rankings from public-split scores
- broad cyber capability measurement

For a detailed claim ledger, see
[`docs/evidence-and-claims.md`](docs/evidence-and-claims.md).

## Quick Start

Prerequisites:

- Python 3.10+
- Git
- Docker and Docker Compose for live HTTP targets or container smoke checks

Install from a fresh clone:

```bash
python3 -m pip install -e .
```

Render a public task:

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

Run the Docker smoke gate:

```bash
python3 scripts/validate_public.py \
  --include-scripted-baseline \
  --include-container-smoke
```

Audit strict v0.0 gates in a maintainer checkout:

```bash
python3 scripts/validate_v0_release.py
```

In a public-only checkout without private holdouts, use:

```bash
python3 scripts/validate_v0_release.py --allow-incomplete
```

That reports gate state without pretending private tasks are public.

## Target Apps

| App | Port | Focus |
| --- | ---: | --- |
| `project_mgmt` | `8011` | project/task tenant boundaries |
| `billing` | `8012` | plan, invoice, and entitlement authorization |
| `support` | `8013` | ticket access, status changes, invite abuse |
| `file_sharing` | `8014` | files, share links, stale-link behavior |
| `api_tokens` | `8015` | tenant-bound tokens and scope checks |
| `audit_settings` | `8016` | audit logs, exports, and admin settings |

Run targets locally:

```bash
docker compose up --build -d
python3 scripts/container_smoke.py
docker compose down
```

Docker request logs are written to `captures/request-logs/`, which is ignored by
Git.

## Evaluate an Agent

`python3 -m authzbench.run` gives an agent a rendered task context and expects a
structured JSON submission.

The runner provides:

- `AUTHZBENCH_CONTEXT`: rendered task context path
- `AUTHZBENCH_SUBMISSION`: output path for `submission.json`
- `AUTHZBENCH_RUN_ID`, `AUTHZBENCH_TASK_ID`, and `AUTHZBENCH_AGENT_ID`: metadata
  used for run tracking and live request-log correlation

Example:

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

- `summary.json`: aggregate counts and v0 evidence metrics
- `<task_id>/submission.json`: agent claims
- `<task_id>/score.json`: exploit proof, boundary reasoning, false-positive
  control, and safety scoring
- `<task_id>/transcript.json`: scorer-owned backend replay evidence
- `<task_id>/target-requests.jsonl`: live request correlation when Docker
  targets and `--target-log-dir` are used

Result bundles under `results/` are local artifacts and are ignored by Git.

## Scoring

For vulnerable tasks, a full pass requires replayable exploit proof, correct
authorization-boundary reasoning, a successful control replay, and safe behavior.
For secure controls, a full pass requires `findings: []`.

Release-facing metrics emphasize:

- `exploit_proven_success_rate`
- `vulnerable_full_pass_count`
- `false_positive_rate`
- `boundary_reasoning_pass_rate`
- `control_execution_pass_rate`
- `authorized_allow_pass_rate`
- `target_request_coverage_rate` for live HTTP runs

The older `mean_score` field remains for compatibility, but it is not the main
release-ranking metric. See [`docs/score-policy.md`](docs/score-policy.md) and
[`docs/leaderboard-schema.md`](docs/leaderboard-schema.md).

## Current Baselines

The baseline registry lives at
[`baselines/baseline-registry.json`](baselines/baseline-registry.json).

Current public-split evidence:

- deterministic scripted harness: 46/46 public tasks
- Kiro `qwen3-coder-next`: two no-tools public runs
- Kiro `claude-haiku-4.5`: two no-tools public runs
- Kiro `claude-sonnet-4.6`: two no-tools public runs
- Kiro `glm-5`: two no-tools public runs
- Kiro `claude-sonnet-4.6` live HTTP tool-agent: two public runs with 46/46
  target-request correlation in both runs

Important interpretation:

- Public-split baselines are useful for methodology and harness comparison.
- They are not private-holdout leaderboard rankings.
- Current no-tools and tool-agent runs still show weak boundary reasoning on
  vulnerable tasks, even when exploit replay succeeds.
- Stale 44-task baselines are retained for historical context only.

See [`docs/status.md`](docs/status.md) and
[`docs/baseline-credibility.md`](docs/baseline-credibility.md).

## Charts and Review Artifacts

Generated public-safe charts live under
[`docs/assets/benchmark-charts/`](docs/assets/benchmark-charts/):

- [Public baseline metrics](docs/assets/benchmark-charts/current-public-baselines.svg)
- [Model pass rate](docs/assets/benchmark-charts/model-pass-rate.svg)
- [Exploit-proven success](docs/assets/benchmark-charts/exploit-proven-success.svg)
- [False-positive rate](docs/assets/benchmark-charts/false-positive-rate.svg)
- [Boundary reasoning](docs/assets/benchmark-charts/boundary-reasoning.svg)
- [Task mix](docs/assets/benchmark-charts/task-mix.svg)
- [Evidence readiness](docs/assets/benchmark-charts/evidence-readiness.svg)

The public task-quality matrix is
[`docs/task-quality-matrix.md`](docs/task-quality-matrix.md). It is an audit aid,
not a leaderboard claim.

## Private Holdouts

Private holdout manifests are intentionally absent from the public repo. The
ignored `tasks_private/holdout/` path is reserved for maintainers to keep hidden
task bodies, seeds, private routes, vulnerability locations, and scorer oracles.

Protected private evidence is published only as redacted aggregate summaries.
Raw private results, captures, panel logs, and holdout manifests must remain
untracked.

Public docs may include count-level private evidence summaries, but must not
publish private task bodies, seeds, routes, oracles, raw captures, or per-task
private result rows.

See [`docs/holdout-and-contamination.md`](docs/holdout-and-contamination.md) and
[`docs/holdout-rotation-protocol.md`](docs/holdout-rotation-protocol.md).

## Release Status

AuthZBench-SaaS is at a released v0.0 stage:

- strict maintainer gate evidence exists
- release notes exist at [`docs/release-notes-v0.0.md`](docs/release-notes-v0.0.md)
- the public `v0.0` tag points to the post-CI release commit
- hosted leaderboard and rotating holdouts are v1/community work

Do not describe the project as leaderboard-ready or as a validated model
benchmark until the hosted or containerized leaderboard process exists.

## Roadmap

The next path is:

1. Add repeated private tool-agent evidence.
2. Expand multi-step workflow realism across more app families.
3. Implement rotating private holdout packs.
4. Add research-grade variance analysis and external review.
5. Build a hosted or fully containerized submission path.
6. Keep release docs and claim boundaries synchronized after every tagged
   release.

See [`ROADMAP.md`](ROADMAP.md).

## Documentation Map

- [`docs/benchmark-card.md`](docs/benchmark-card.md): intended use and limits
- [`docs/evidence-and-claims.md`](docs/evidence-and-claims.md): current claim ledger
- [`docs/authzbench-saas-v0.0-technical-report.md`](docs/authzbench-saas-v0.0-technical-report.md): technical report draft
- [`docs/authzbench-saas-v0.0-evidence-map.md`](docs/authzbench-saas-v0.0-evidence-map.md): claim-to-evidence map
- [`docs/methodology.md`](docs/methodology.md): scoring methodology
- [`docs/result-schema.md`](docs/result-schema.md): result artifact schema
- [`docs/leaderboard-schema.md`](docs/leaderboard-schema.md): leaderboard row schema
- [`docs/score-policy.md`](docs/score-policy.md): headline metric policy
- [`docs/score-stability-policy.md`](docs/score-stability-policy.md): score/version policy
- [`docs/task-quality-rubric.md`](docs/task-quality-rubric.md): task-quality review rubric
- [`docs/task-quality-matrix.md`](docs/task-quality-matrix.md): public task-quality matrix
- [`docs/v0-release-plan.md`](docs/v0-release-plan.md): v0 release criteria
- [`docs/publish-checklist.md`](docs/publish-checklist.md): publication checks
- [`docs/agent-evaluator-kit.md`](docs/agent-evaluator-kit.md): third-party agent guide
- [`CONTRIBUTING.md`](CONTRIBUTING.md): contribution rules
- [`SECURITY.md`](SECURITY.md): safe handling guidance
- [`CITATION.cff`](CITATION.cff): citation metadata

## License

MIT. See [`LICENSE`](LICENSE).
