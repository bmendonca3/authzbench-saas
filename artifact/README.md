# AuthZBench-SaaS Artifact Packet

This directory is the public reproducibility packet scaffold for the released
`v0.0` benchmark artifact. It should remain public-safe: no private holdout
bodies, raw private results, captures, credentials, or raw panel logs belong
here.

## Contents

- `install.md`: local setup and prerequisites.
- `run-public-validation.sh`: bounded public validation entrypoint.
- `expected-output/`: public-safe expected outputs for stable validation
  signals, including the deterministic public view of v1 readiness.
- `run-bundle.md`: guidance for packaging and checking submitted run evidence.
- `hosted-submission-execution-runbook.json`: public-safe runbook for the
  maintainer-hosted or fully containerized release-candidate smoke path. It is
  not hosted execution evidence and cannot satisfy strict v1 readiness by
  itself.
- `private-holdout-rotation-metadata.template.json`: public-safe template for
  maintainer-only private-pack rotation metadata. It is not private holdout
  evidence and cannot satisfy strict v1 readiness.
- `private-holdout-operation-runbook.json`: public-safe runbook for operating
  active plus shadow/candidate private packs. It is not private holdout
  evidence and cannot satisfy strict v1 readiness by itself.
- `v1-paper-readiness-runbook.json`: public-safe runbook for the final v1
  report and IEEE scaffold refresh. It is not release-candidate paper
  readiness evidence and cannot satisfy strict v1 readiness by itself.
- `submission-runner-smoke.template.json`: public-safe release-candidate
  hosted/containerized smoke evidence template. It is not smoke evidence and
  cannot satisfy strict v1 readiness.
- `v1-task-scale-roadmap.json`: public-safe planning roadmap for the path from
  54 public tasks to at least 100 total public plus protected-private tasks. It
  is not task-scale evidence and cannot satisfy strict v1 readiness by itself.
- `v1-release-candidate-validation.template.json`: public-safe template for
  external release evidence. It is not release evidence and cannot satisfy
  strict v1 readiness.
- `v1-release-candidate-validation-runbook.json`: public-safe runbook for
  collecting final release-candidate validation evidence. It is not release
  evidence and cannot satisfy strict v1 readiness by itself.

## Public Validation

Run the public validation entrypoint from the repository root:

```bash
artifact/run-public-validation.sh
```

The script runs the public validation gate, baseline registry validation,
leaderboard submission validation, and the tracked-path privacy check. Its final
line should be:

```text
Artifact privacy check passed: no private/raw artifact paths are tracked.
```

Paper table reproducibility is checked separately:

```bash
python3 scripts/generate_paper_tables.py
git diff --exit-code -- paper/shared
```

The public v1-readiness snapshot is checked with:

```bash
python3 scripts/validate_v1_readiness.py \
  --allow-incomplete \
  --public-view \
  --expected-output artifact/expected-output/v1-readiness-public-view.json
```

`--public-view` intentionally ignores ignored/private checkout state. This keeps
the public artifact result reproducible in a clean clone and prevents a local
private pack from changing the public expected output. The expected fixture
must continue to report `v1_ready: false` until the public claim boundary and
tracked artifact state genuinely change. Maintainer-only strict readiness uses
the private checkout and external release evidence instead.

The expected-output fixtures in `artifact/expected-output/` summarize stable
public-safe signals only. They are not raw run bundles.

## Containerized Submission Isolation Smoke

Docker-backed public validation also runs an ephemeral rehearsal of the future
submission path. The submitter container receives only rendered context and a
writable output directory. It runs without network access, with a read-only
root filesystem, dropped capabilities, `no-new-privileges`, a non-root user,
and resource limits. Private manifests remain in the scorer-controlled host
process.

The CI rehearsal proves the mechanism only. It deliberately emits
`execution_scope: rehearsal` and cannot satisfy the v1 hosted-execution gate.
Release evidence must rerun the command against the active private pack with
`execution_scope: release_candidate`, the active pack version, and the matching
private-pack fingerprint:

```bash
python3 scripts/containerized_submission_smoke.py \
  --private-pack tasks_private/holdout/<active-pack> \
  --output artifact/submission-runner-smoke.json \
  --benchmark-source-sha "$(git rev-parse HEAD)" \
  --private-pack-version <active-pack-version> \
  --execution-scope release_candidate
```

If the runner image is not already present locally, the smoke runner pulls it
before recording `runner_image_or_hosted_version`; use `--image` to point at a
different pinned runner image.

Use `artifact/submission-runner-smoke.template.json` only as a starting shape
for that release-candidate record. Replace every placeholder with real
maintainer-platform or containerized smoke evidence before writing
`artifact/submission-runner-smoke.json`. The validator rejects the template if
it is copied unchanged, and it also rejects angle-bracket placeholders embedded
inside required fields such as `runner:<digest>` or `--private-pack <active-pack>`.

Use `artifact/hosted-submission-execution-runbook.json` as the public-safe
procedure checklist for that release-candidate smoke. The readiness validator
checks that the runbook defines hosted and fully containerized modes, required
private inputs, isolation controls, required smoke fields, and publication
rules. A valid runbook still does not satisfy the hosted-execution gate; only
passed `execution_scope: release_candidate` evidence tied to the active private
pack can do that.

The tracked `artifact/submission-runner-smoke.json` file is allowed to contain a
public-safe blocker record while the active private pack and maintainer-platform
release smoke are not available. That blocker record is structured evidence for
what remains missing; it is not a passing hosted/containerized submission smoke
and the v1 readiness validator keeps the release gate red until it is replaced
by passed `execution_scope: release_candidate` evidence. Its public rehearsal
reference must mark `reference_scope: prior_public_checkpoint` and include an
AuthZBench-SaaS Actions URL and matching numeric run ID, plus workflow name
`Validate AuthZBench-SaaS`, so the cited CI evidence is directly inspectable.

## Private Operation Blocker

The tracked `artifact/private-holdout-operation-blocker.json` file is
public-safe blocker evidence for the private-operation cluster. It documents the
remaining need for active and shadow/candidate private packs, active-pack
fingerprinting, repeated private tool-agent and no-tools rows, and at least 100
validated total tasks.

This file intentionally does not contain private manifests, private task IDs,
private routes, private seeds, raw private outputs, captures, credentials, or
local absolute paths. It cannot satisfy the private-holdout, private-evidence,
or scale gates; it only makes the current blocker explicit and reproducible in
the public readiness fixture. Its public readiness reference must mark
`reference_scope: prior_public_checkpoint` and include an AuthZBench-SaaS
Actions URL and matching numeric run ID, plus workflow name `Validate
AuthZBench-SaaS`.

Use `artifact/private-holdout-rotation-metadata.template.json` only as a
starting shape for the ignored maintainer-only file
`tasks_private/holdout/rotation-metadata.json`. Replace every placeholder with
real active and shadow/candidate pack metadata, then validate in the private
checkout. The v1 readiness validator rejects the template if it is copied
unchanged into the private rotation metadata path. The populated metadata must
declare concrete pack versions, lowercase SHA-256 fingerprints that match each
computed pack fingerprint, a concrete compatibility policy, non-placeholder
retirement triggers, and a rerun policy that requires both no-tools and
tool-agent baselines before current comparison.

Use `artifact/private-holdout-operation-runbook.json` as the public-safe
procedure checklist for private-pack operation. The readiness validator checks
that the runbook names required private inputs, operation steps, rotation
metadata fields, acceptance checks, and publication rules. A valid runbook still
does not satisfy the rotating-private-holdout gate; only validated active plus
shadow/candidate packs with real ignored rotation metadata can do that.

Use `artifact/v1-task-scale-roadmap.json` as count-level planning evidence for
the v1 scale path. It currently maps the 54 public tasks plus two 24-task
protected-private pack waves to 102 planned total tasks. It does not contain or
prove private manifests, and the v1 readiness validator still keeps the
`v1_task_scale` gate red until actual public plus validated private manifest
counts reach at least 100.

Use `artifact/v1-paper-readiness-runbook.json` as the public-safe procedure
checklist for the final report and IEEE scaffold refresh. The readiness
validator checks that the runbook names the required upstream review and
infrastructure inputs, refresh steps, commands, acceptance checks, and
publication rules. A valid runbook still does not satisfy the
`paper_and_artifact_readiness` gate; that gate requires release-candidate
evidence in `docs/v1-paper-readiness.json` after the upstream gates are
complete, including the exact paper-table refresh, chart refresh, chart diff,
paper-table diff, and `latexmk` commands plus concrete LaTeX result and
`YYYY-MM-DD` verification date.

## Release-Candidate Evidence Template

Strict v1 readiness requires release evidence supplied with:

```bash
python3 scripts/validate_v1_readiness.py \
  --release-evidence <external-json>
```

Use `artifact/v1-release-candidate-validation.template.json` only as a starting
shape. Copy it outside tracked Git, replace every placeholder with real
release-candidate evidence, and keep private task internals out of the public
artifact packet. The validator rejects the template if it is passed directly as
release evidence.

Use `artifact/v1-release-candidate-validation-runbook.json` as the public-safe
procedure checklist for collecting that external release evidence. The
readiness validator checks that the runbook names required inputs, required
commands, evidence fields, acceptance checks, and publication rules. A valid
runbook still does not satisfy the final release-candidate gate; strict
readiness requires an external evidence file passed with `--release-evidence`
from a clean working tree. That external evidence must include an AuthZBench-SaaS
release-evidence schema version, exact-head GitHub Actions URL, numeric run ID
matching that URL, workflow name `Validate AuthZBench-SaaS`, the run's
`headSha` matching the release commit, and non-placeholder evidence plus exit
code `0` for every required command. Required commands include the public-view
v1 readiness fixture check:

```bash
python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view \
  --expected-output artifact/expected-output/v1-readiness-public-view.json
```

The tracked private/raw path scan must record evidence exactly as
`empty output`.

## Claim Boundary

This artifact packet supports public reproduction of the inspectable public
split. It does not make the repository a hosted leaderboard and does not expose
private holdout tasks.
