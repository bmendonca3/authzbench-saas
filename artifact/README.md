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

## Claim Boundary

This artifact packet supports public reproduction of the inspectable public
split. It does not make the repository a hosted leaderboard and does not expose
private holdout tasks.
