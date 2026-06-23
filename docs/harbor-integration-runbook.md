> [!NOTE]
> **Consolidation Notice**: This file is slated for consolidation. Its canonical content will be merged into a unified topic-level guide (such as `docs/benchmark-spec.md` or `docs/scoring-and-submissions.md`) in subsequent consolidation phases.

# Harbor Integration Runbook

Status: public-safe v1-prep design and implementation target. This file
records scoped repo-side Harbor local smoke/parity evidence, but does not claim
Harbor platform acceptance, external review completion, hosted leaderboard
readiness, or `v1` external readiness.

## Public Harbor Facts Used

This runbook is based on public Harbor documentation only:

- Harbor describes itself as a framework for evaluating agents in sandboxed
  environments. For this generated skeleton, use the checked-in reference
  config from inside the generated dataset directory.
- A Harbor dataset is a collection of tasks. A task has an instruction,
  environment, and test script.
- Harbor task directories include `instruction.md`, `task.toml`,
  `environment/`, optional `solution/`, and `tests/test.sh`.
- Harbor jobs produce job-level config/result files and trial-level agent and
  verifier artifacts, including agent trajectories and verifier outputs.
- Harbor automatically collects files written under `/logs/artifacts/`.
- Harbor supports separate verifier environments, which is the public
  mechanism that most closely matches AuthZBench-SaaS scorer-controlled private
  replay.

Public references:

- https://github.com/harbor-framework/harbor
- https://www.harborframework.com/docs/run-jobs/run-evals
- https://www.harborframework.com/docs/tasks
- https://www.harborframework.com/docs/run-jobs/results-and-artifacts

## Claim Boundary

Repo-side Harbor compatibility helpers, local Harbor smoke, and local per-task
reward parity have been verified for the Harbor-compatible execution target
(see the parity experiment section below). Harbor platform acceptance,
publishing, and endorsement are external gates and are not claimed.

Do not describe this as:

- Harbor platform acceptance or endorsement;
- a hosted leaderboard;
- completed external review;
- passing private hosted execution;
- `v1-ready` evidence in the external sense.

The current public-view readiness fixture reports `v1_ready: false` with
1 unmet gate in `artifact/expected-output/v1-readiness-public-view.json`.
This is scoped to the internal/public-view readiness gates only and does not
assert Harbor acceptance or any other external validation. See
[`claims-and-evidence.md`](claims-and-evidence.md).

Repo-side adapter compatibility, local Harbor smoke, and local per-task parity
are complete for the public package. The remaining Harbor-specific blockers are
platform review, publishing, organization sharing, and any host-specific
packaging requirements.

### Harbor status table

| Level | Status | Evidence |
| --- | --- | --- |
| Repo-side local adapter | Complete | `authzbench_harbor/` package, `artifact/harbor-adapter-contract.json` |
| Local smoke | Complete | `artifact/harbor-adapter-smoke.json`, `artifact/harbor-local-execution-smoke.json` |
| Parity methodology | Complete (local, 6-task public subset) | `artifact/harbor-parity-experiment.json` |
| Platform acceptance | Blocked | `artifact/harbor-adapter-readiness-blockers.json` |
| Hosted leaderboard / external review | Deferred to v2 | Not claimed; v2 external validation track |

The repo-side local adapter, local smoke, and parity methodology are
public-safe and reviewer-verifiable. Platform acceptance is blocked on
SDK adapter API integration, adapter metadata, and multi-task parity
evidence. Hosted leaderboard operation and external review are deferred
to v2.

## Current Repo-Side Adapter State

This section describes the adapter surface that ships on `main` today,
distinct from the future packaged SDK adapter target described in the
sections below. The repository currently ships a `authzbench_harbor/`
Python package that wraps the skeleton builder and exposes a CLI. The
package is the repo-side compatibility helper described in
`artifact/harbor-adapter-contract.json`. A future Harbor-hosted publication may
still require platform-specific wrapping, review, or sharing outside this repo.

Package modules on `main`:

- `authzbench_harbor/__init__.py` — package marker and `ADAPTER_VERSION`.
- `authzbench_harbor/adapter.py` — `build_dataset(...)` entrypoint that
  wraps the skeleton builder and persists the dataset manifest.
- `authzbench_harbor/cli.py` — `python3 -m authzbench_harbor.cli build`
  command, with the flags documented below.
- `authzbench_harbor/scorer_bridge.py` — translates AuthZBench-SaaS
  scorer output into Harbor verifier reward format.
- `authzbench_harbor/redaction.py` — public-safety scan for generated
  artifacts.
- `authzbench_harbor/schemas.py` — public-safe schema constants used by
  the adapter and the parity validator.

Current CLI usage (mirrors the docstring in
`authzbench_harbor/cli.py`):

```bash
python3 -m authzbench_harbor.cli build \
    --tasks 'tasks/**/*.json' \
    --output-dir artifact/harbor-dataset-public-smoke \
    --harness-lane no_tools \
    --limit 6 \
    --overwrite

python3 -m authzbench_harbor.cli build \
    --task-id pm_same_tenant_read_control \
    --output-dir artifact/harbor-dataset-single \
    --harness-lane no_tools \
    --overwrite
```

Supported CLI flags:

- `--tasks` (repeatable): one or more glob patterns over task manifests.
- `--output-dir` (required): destination directory for the generated
  Harbor dataset.
- `--harness-lane` (required): `no_tools` or `live_http_tool_agent`.
- `--limit` (optional): cap the number of tasks included in the
  generated dataset.
- `--overwrite` (optional): replace an existing generated output
  directory.
- `--task-id` (optional, singular): include a single task id.
- `--task-ids` (optional, repeatable): comma-separated list of task
  ids (compatibility alias for subset generation).
- `--benchmark-source-sha` (optional): override the recorded benchmark
  source SHA (defaults to `git rev-parse HEAD`).

## Parity Methodology

The parity experiment artifact (`artifact/harbor-parity-experiment.json`) carries
an explicit `parity_methodology` field. Two methodologies are supported:

- `per_task_pairing` (default for new evidence): the validator requires
  complete per-task reward/score maps, recomputes `per_task_match_count`,
  `per_task_match_rate`, and `per_task_disagreements` from those maps, and
  enforces a strict `reward_tolerance` (default `1e-5`) on
  `abs(native_score - harbor_reward)`. `parity_verified` is set to `true`
  only when `per_task_match_rate >= required_match_rate` (default `1.0`)
  and `per_task_disagreements` is empty.
- `aggregate_means` (back-compat only): the validator accepts this only
  when `evidence_status` is `historical_backcompat`, since aggregate-only
  parity cannot prove per-task equality.

The existing committed parity evidence predates per-task reward extraction
and is preserved as historical aggregate-means evidence. New parity evidence
generated by `scripts/run_harbor_parity_experiment.py` always uses
`per_task_pairing` and `evidence_status: current`.

### Local Parity Experiment Results

The local parity experiment has been executed and verified with 100% matching results under the `per_task_pairing` methodology:

| Metric | Value | Notes |
| --- | --- | --- |
| **Parity Verified** | `true` | Exact per-task match |
| **Task Count** | 6 | 3 Vulnerable, 3 Secure Control |
| **Match Rate** | 1.0 (6 / 6) | 100% task-by-task match |
| **Harbor Reward Mean** | 0.500 | Matching native score mean |
| **Native Score Mean** | 0.500 | Matching Harbor mean |
| **Disagreements** | None | Zero reward discrepancies |
| **Harbor Run ID** | `d277f128-0af1-4b48-8d01-3c7b509cda28` | Real local Harbor execution |


### Schema fields

| Field | Required when | Notes |
| --- | --- | --- |
| `parity_methodology` | `parity_verified: true` | `per_task_pairing` or `aggregate_means` (historical only) |
| `evidence_status` | always | `current`, `historical_backcompat`, or `blocked` |
| `reward_tolerance` | `per_task_pairing` | Default `1e-5`; values above the default are rejected |
| `required_match_rate` | `per_task_pairing` | Default `1.0` |
| `harbor_per_task_rewards` | `per_task_pairing` | Map of `task_id -> reward` for every `task_id` |
| `native_per_task_scores` | `per_task_pairing` | Map of `task_id -> score` for every `task_id` |
| `per_task_match` | `per_task_pairing` | Recomputed by the validator; order does not matter |
| `per_task_match_count` | `per_task_pairing` | Recomputed by the validator |
| `per_task_match_rate` | `per_task_pairing` | Recomputed by the validator |
| `per_task_disagreements` | `per_task_pairing` | Recomputed by the validator; empty when `parity_verified: true` |
| `parity_match_threshold` | `per_task_pairing` | Match-rate threshold (typically `1.0`); kept for back-compat |
| `methodology_note` | recommended | Free-form note describing the methodology context |

### Failure example

```json
{
  "parity_methodology": "aggregate_means",
  "parity_verified": true
}
```

This is invalid unless `evidence_status: "historical_backcompat"` is set.
The validator emits:

> `parity_verified=true with parity_methodology='aggregate_means' requires evidence_status='historical_backcompat'`

The current parity experiment that consumes the generated dataset has been
extended to record per-task Harbor reward values alongside the native
AuthZBench-SaaS scores, so the parity evidence now includes
`harbor_per_task_rewards`, `native_per_task_scores`, `per_task_match`,
`per_task_match_count`, `per_task_match_rate`,
`per_task_disagreements`, and `parity_match_threshold`. The aggregate
mean-only comparison is still present for back-compat.

This section claims only scoped local Harbor smoke/parity evidence for the
public repo-side adapter surface. It does not claim Harbor platform acceptance,
hosted leaderboard readiness, or v1 external-readiness evidence.

## Target Dataset Shape

The Harbor dataset should be generated from AuthZBench-SaaS manifests rather
than hand-maintained as a second source of truth.

Target builder responsibilities:

- read public task manifests from `tasks/*/*.json`;
- optionally read maintainer-only private manifests outside public Git;
- render one Harbor task directory per AuthZBench-SaaS task;
- write root-level `dataset.toml` with generated task references, public-safe
  dataset metadata, and explicit non-evidence flags for Harbor publishing and
  execution;
- write root-level `dataset-manifest.json` as the AuthZBench-SaaS skeleton
  manifest consumed by local validators;
- write `instruction.md` from the existing rendered task context;
- write `task.toml` with Harbor task schema version `1.3`, Harbor config
  tables, public-safe AuthZBench-SaaS metadata under `[metadata.authzbench]`,
  resource requirements, network policy, artifact paths, and verifier settings;
- write `environment/Dockerfile` and `solution/solve.sh` so generated task
  directories match the public Harbor adapter shape, while keeping
  `solution/solve.sh` as a fail-closed placeholder until a verified public
  oracle exists;
- include a task-local verifier entrypoint that invokes the AuthZBench-SaaS
  scorer bridge;
- write a reference `run_authzbench_saas.yaml` for future local Harbor
  structure/oracle checks without claiming the run has passed;
- never write private task bodies, routes, seeds, or oracles into public Harbor
  task directories.

For private execution, task names and metadata must remain redacted or
count-level unless the active release policy explicitly permits publication.

## SDK Adapter Expectations

A future Harbor SDK adapter should expose these internal seams:

| Component | Expected responsibility |
| --- | --- |
| Dataset builder | Convert AuthZBench-SaaS manifests into Harbor dataset/task directories without duplicating benchmark truth. |
| Task context renderer | Render the same `context.json` contract used by `python3 -m authzbench.run`. |
| Runner bridge | Invoke the Harbor agent/model lane and pass only rendered context plus output paths. |
| Output collector | Read agent output from `/logs/artifacts/submission.json` or the declared Harbor artifact path. |
| Verifier/scorer bridge | Run scorer-controlled backend replay and write Harbor-compatible verifier reward and logs. |
| Metadata normalizer | Emit benchmark source SHA, fingerprint, comparability key, harness type, model, agent, tool access, timeout, and private-pack version/fingerprint when applicable. |
| Redaction policy | Publish public summaries only; keep private manifests, raw private outputs, captures, credentials, and local paths out of tracked artifacts. |

The adapter should fail closed when required metadata is missing. It should not
invent task outcomes, target-request coverage, private-pack fingerprints, or
review evidence.

Expected package/module surface for the repo-side adapter checkout:

- `authzbench_harbor/__init__.py`, `adapter.py`, `cli.py`, `redaction.py`,
  `schemas.py`, and `scorer_bridge.py`;
- `artifact/harbor-adapter-metadata.json`,
  `artifact/harbor-parity-experiment.json`, and
  `artifact/harbor-adapter-smoke.json`;
- generated public smoke dataset files under
  `artifact/harbor-dataset-public-smoke/`, including `dataset.toml`,
  `dataset-manifest.json`, and `run_authzbench_saas.yaml`;
- module entrypoint
  `python3 -m authzbench_harbor.cli build --output-dir <generated-harbor-dataset-path>`;
- CLI support for `--output-dir`, `--limit`, `--overwrite`,
  `--harness-lane`, `--task-id`, and `--task-ids`.

The current repository has a `authzbench_harbor/` package that ships as the
repo-side compatibility wrapper. Harbor platform acceptance and publishing
remain outside this claim:

See [Current Repo-Side Adapter State](#current-repo-side-adapter-state) above for the CLI surface that ships on `main` today.

```bash
python3 scripts/build_harbor_dataset_skeleton.py \
  --task 'tasks/*/*.json' \
  --output-dir <generated-harbor-dataset-path> \
  --task-ids <comma-separated-task-ids> \
  --limit <n> \
  --overwrite
```

This helper writes a public-safe `dataset.toml`, skeleton task directories, and
placeholder package-shape files. It does not produce `adapter_metadata.json`,
`parity_experiment.json`, a real Harbor package, Harbor publish evidence, or
Harbor execution evidence.

The machine-readable version of this target is tracked at
[`artifact/harbor-adapter-contract.json`](../artifact/harbor-adapter-contract.json)
and validated with:

```bash
python3 scripts/validate_harbor_integration.py
```

That validator checks the public-safe contract shape only. It does not execute
Harbor and cannot close the SDK integration gate by itself.

Harbor adapter-readiness blockers are tracked separately at
[`artifact/harbor-adapter-readiness-blockers.json`](../artifact/harbor-adapter-readiness-blockers.json)
and validated with:

```bash
python3 scripts/validate_harbor_adapter_blockers.py
```

That blocker record covers adapter metadata, parity experiment evidence, local
Harbor execution evidence, and adapter review/publish evidence that must remain
blocked until real runs and review artifacts exist.

Public-safe templates for future adapter metadata and parity artifacts are:

```bash
python3 scripts/validate_harbor_adapter_templates.py
```

The templates live at
[`artifact/harbor-adapter-metadata.template.json`](../artifact/harbor-adapter-metadata.template.json)
and
[`artifact/harbor-parity-experiment.template.json`](../artifact/harbor-parity-experiment.template.json).
They define the required future artifact shapes only. They do not contain real
adapter metadata, Harbor run IDs, parity rows, review findings, or release
evidence.

The public-only skeleton builder is:

```bash
python3 scripts/build_harbor_dataset_skeleton.py \
  --task 'tasks/*/*.json' \
  --output-dir <generated-harbor-dataset-path> \
  --harness-lane no_tools
```

For live HTTP tool-agent planning, use `--harness-lane live_http_tool_agent`.
Use repeatable `--task-id <id>` for subset generation. `--overwrite` is an
alias for replacing an existing generated output directory. `--task-ids` is a
comma-separated compatibility alias for future Harbor adapter packaging. The
builder writes Harbor-shaped task directories, `dataset.toml`, and a reference
`run_authzbench_saas.yaml`, but it does not invoke Harbor, publish a dataset, or
create private execution evidence.

Validate a generated skeleton with:

```bash
python3 scripts/validate_harbor_dataset_skeleton.py \
  --dataset-dir <generated-harbor-dataset-path>
```

This checks the public skeleton structure and redaction boundary. It still does
not run Harbor.

Check local readiness to attempt a future Harbor run with:

```bash
python3 scripts/check_harbor_local_execution.py
```

That preflight generates and validates a temporary public skeleton and checks
whether the Harbor CLI is on `PATH`. It does not invoke `harbor run`. In a
checkout without Harbor installed, it records the local execution gate as
blocked on the missing CLI/package.

When Harbor is installed and a generated public skeleton has been reviewed, the
reference command target is:

```bash
cd <generated-harbor-dataset-path> && harbor run -c run_authzbench_saas.yaml --yes
```

To create a redacted local smoke summary without committing raw `harbor-jobs/`
output, run:

```bash
python3 scripts/run_harbor_local_smoke.py
python3 scripts/validate_harbor_local_evidence.py
```

The checked-in smoke summary proves only local task/agent/verifier execution for
the generated public skeleton. It uses an explicit public secure-control oracle
solution that writes `findings: []`, then records whether Harbor verifier reward
matches the native AuthZBench-SaaS scorer reward for that one control task.
It deliberately records `parity_verified: false` until a public-safe adapter can
produce valid submissions across vulnerable and secure-control tasks and a
multi-task `parity_experiment.json` is computed from matching Harbor and native
run artifacts.

## No-Tools Lane

For no-tools model runs, Harbor should receive an instruction-only task context
and write a structured AuthZBench-SaaS `submission.json`.

Expected output rule:

- vulnerable tasks require replayable finding evidence;
- secure controls require `findings: []`;
- unsupported prose without a replayable request must not score as proof.

The verifier bridge should translate the AuthZBench-SaaS score into Harbor
reward output while preserving scorer-derived fields in redacted artifacts.

## Live HTTP Tool-Agent Lane

For live HTTP tool-agent runs, Harbor must orchestrate or attach the target SaaS
services before the agent phase and preserve request-log correlation.

Required lane metadata:

- target service image or compose source;
- target startup healthcheck;
- agent network policy;
- `AUTHZBENCH_AGENT_ID` or equivalent request-correlation identity;
- target-request coverage summary;
- scorer replay result;
- public-safe plan/probe artifact references when available.

If Harbor cloud providers cannot support the current Docker Compose shape, the
adapter should use a single prebuilt target image or a documented hosted target
service, then record that as an implementation blocker until verified.

## Verifier And Oracle Boundary

The verifier must be scorer-controlled. For public tasks this means the Harbor
test script may call the AuthZBench-SaaS scorer with public manifests. For
private tasks, the agent environment must not receive private manifests, seeds,
routes, or oracle fields.

Preferred private execution shape:

- agent environment receives rendered context only;
- verifier environment is separate or otherwise protected;
- private manifests are readable only by scorer-controlled code;
- scorer writes raw private evidence to ignored/protected storage;
- `/logs/artifacts/` receives only redacted summaries and agent submission
  artifacts that are safe to publish.

## Harbor Job Artifact Mapping

Harbor job/trial output should map into the existing AuthZBench-SaaS run-bundle
contract:

| Harbor artifact | AuthZBench-SaaS use |
| --- | --- |
| job `config.json` | Run configuration, agent, model, dataset version, environment provider. |
| job `result.json` | Aggregate status, trial count, pass/fail summary. |
| trial `config.json` | Task id or redacted task handle, timeout, resource policy. |
| trial `result.json` | Task-level Harbor reward and verifier status. |
| trial `agent/trajectory.json` | Agent trajectory evidence for debugging and tool-use audit. |
| trial `verifier/reward.txt` or `reward.json` | Harbor reward derived from AuthZBench-SaaS scorer output. |
| trial `verifier/test-stdout.txt` and `test-stderr.txt` | Scorer bridge logs, redacted before publication. |
| trial `artifacts/submission.json` | Agent submission consumed by the scorer bridge. |

The public run bundle must also preserve:

- benchmark source SHA;
- benchmark fingerprint;
- comparability key;
- source-summary hashes;
- run IDs and repeated-run source IDs;
- target-request coverage for tool-agent runs;
- private-pack version and active private-pack fingerprint for private runs;
- redaction and privacy-scan status.

## Gate Status

Repo-side Harbor preparation is partial:

- Public-safe Harbor mapping: this runbook.
- Validator hardening: generic absolute-path rejection in redacted protected
  evidence and stricter embedded-placeholder checks in release-facing runbook
  lists and smoke evidence.
- Local private holdout observation: one aggregate 24-task pack can validate in
  this checkout, but rotating holdouts still require a separate shadow or
  candidate pack plus rotation metadata.

Blocked before this can become release evidence:

- exact Harbor SDK adapter API integration;
- adapter metadata and parity experiment evidence;
- multi-task vulnerable/control Harbor parity evidence from a public-safe
  submission-producing adapter;
- active and shadow/candidate private pack operation;
- protected release-candidate hosted/containerized smoke;
- repeated private no-tools and tool-agent rows;
- external review lanes;
- strict release evidence.
