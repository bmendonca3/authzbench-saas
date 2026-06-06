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
- 44 public benchmark tasks
- 18 vulnerable tasks
- 26 secure-control tasks
- 10 authorized-allow controls
- deterministic backend replay scoring
- target-side request logging for Docker runs
- public baseline summaries for scripted and model runs
- protected private-holdout evidence summarized without private task leakage
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

Current public-split snapshot:

- scripted harness checks pass all 44 public tasks
- repeated model baselines cover 5 required model/agent families
- current model runs pass 25-29 of 44 public tasks
- the public live HTTP tool-agent baseline has 44/44 target-request correlation
- one public model run currently shows a non-zero false-positive rate; most do
  not

These are public-split results only. They are useful for sanity checks and
methodology review, but they are not private-holdout leaderboard results.

Current registry status:

- 5 of 5 required repeated model/agent families
- accepted current public live HTTP tool-agent baseline
- `v0_baseline_ready: true`

That status covers only the baseline registry. Full v0-candidate readiness also
depends on private holdouts, leaderboard-submission evidence, release evidence,
privacy checks, and sectional review gates.

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

## v0 Candidate Status

AuthZBench-SaaS is a release candidate for v0, not a tagged v0 release.
Maintainer strict validation currently passes with the private holdout pack
present, but no v0 tag or hosted public leaderboard has been published.

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
- [`docs/v0-release-plan.md`](docs/v0-release-plan.md): release criteria
- [`docs/benchmark-card.md`](docs/benchmark-card.md): intended use and limits
- [`docs/baseline-credibility.md`](docs/baseline-credibility.md): baseline bar
- [`docs/leaderboard-schema.md`](docs/leaderboard-schema.md): leaderboard format
- [`docs/publish-checklist.md`](docs/publish-checklist.md): publication checks
- [`SECURITY.md`](SECURITY.md): safe handling guidance

## License

MIT. See [`LICENSE`](LICENSE).
