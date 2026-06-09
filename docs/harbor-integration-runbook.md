# Harbor Integration Runbook

Status: public-safe v1-prep design and implementation target. This file does
not claim Harbor hosted execution, Harbor acceptance, external review
completion, hosted leaderboard readiness, or `v1` readiness.

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

AuthZBench-SaaS can be shaped as a Harbor-compatible execution target, but this
repository does not yet contain a verified Harbor adapter or a passing Harbor
job. The current state is an implementation plan plus local validator hardening.

Do not describe this as:

- Harbor platform acceptance or endorsement;
- a hosted leaderboard;
- completed external review;
- passing private hosted execution;
- `v1-ready` evidence.

The adapter remains blocked until exact Harbor SDK/package APIs are integrated
and tested against a real Harbor local run.

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

Expected package/module surface for a real adapter checkout:

- `pyproject.toml`, `README.md`, `adapter_metadata.json`,
  `parity_experiment.json`, `dataset.toml`, and `run_authzbench_saas.yaml`;
- `src/authzbench_saas_harbor/main.py` with a module entrypoint equivalent to
  `uv run python -m authzbench_saas_harbor.main --output-dir <generated-harbor-dataset-path>`;
- `src/authzbench_saas_harbor/adapter.py` for parsing benchmark manifests and
  generating task directories;
- task templates for `task.toml`, `instruction.md`,
  `environment/Dockerfile`, `solution/solve.sh`, and `tests/test.sh`;
- CLI support for `--output-dir`, `--limit`, `--overwrite`, and `--task-ids`.

The current repository has a compatibility helper, not a packaged Harbor SDK
adapter:

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
whether the `harbor` CLI is on `PATH`. It does not invoke `harbor run`. In a
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
the generated public skeleton. It deliberately records `parity_verified: false`
until a submission-producing public-safe agent or adapter and matching native
AuthZBench-SaaS run evidence exist.

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
- passing local Harbor run;
- local Harbor CLI/package availability for verified run attempts;
- adapter metadata and parity experiment evidence;
- active and shadow/candidate private pack operation;
- protected release-candidate hosted/containerized smoke;
- repeated private no-tools and tool-agent rows;
- external review lanes;
- strict release evidence.
