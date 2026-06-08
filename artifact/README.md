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
- `submission-runner-smoke.template.json`: public-safe release-candidate
  hosted/containerized smoke evidence template. It is not smoke evidence and
  cannot satisfy strict v1 readiness.
- `v1-release-candidate-validation.template.json`: public-safe template for
  external release evidence. It is not release evidence and cannot satisfy
  strict v1 readiness.

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

Use `artifact/submission-runner-smoke.template.json` only as a starting shape
for that release-candidate record. Replace every placeholder with real
maintainer-platform or containerized smoke evidence before writing
`artifact/submission-runner-smoke.json`. The validator rejects the template if
it is copied unchanged.

The tracked `artifact/submission-runner-smoke.json` file is allowed to contain a
public-safe blocker record while the active private pack and maintainer-platform
release smoke are not available. That blocker record is structured evidence for
what remains missing; it is not a passing hosted/containerized submission smoke
and the v1 readiness validator keeps the release gate red until it is replaced
by passed `execution_scope: release_candidate` evidence.

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
the public readiness fixture.

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

## Claim Boundary

This artifact packet supports public reproduction of the inspectable public
split. It does not make the repository a hosted leaderboard and does not expose
private holdout tasks.
