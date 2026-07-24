# Validation Commands

This page consolidates the bounded public validation set, the maintainer-only
strict set, and the privacy check. It is intentionally a copy-paste friendly
reference; see the linked scripts for full flag documentation.

## Validation Levels

Reviewers and hosts should use the appropriate validation level:

### Public No-Docker Reviewer Validation
Run this from a clean clone to verify public tests and registry states:
```bash
python3 scripts/validate_public.py --include-scripted-baseline
```

The runner includes the public-view readiness check:
```bash
python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view --expected-output artifact/expected-output/v1-readiness-public-view.json
```

This is a fixture-matching public-view check: `--allow-incomplete` returns 0
when the rendered output matches the expected fixture, even if `v1_ready` is
false under honest post-cleanup evidence (for example, release-affecting docs
changed after the pinned `benchmark_source_sha`). This is not a claim of
external validation or full v1 readiness; v2 external validation remains
deferred.

### Docker / Container-Smoke Validation
Run this to include full container smoke testing (requires Docker to be running):
```bash
python3 scripts/validate_public.py --include-scripted-baseline --include-container-smoke
```

### Host-Presentation Validation
To run the aggregate validation checking all host-facing artifacts, markdown links, templates, and schemas:
```bash
python3 scripts/validate_host_presentation.py
```
Or, to run the aggregate checks including Docker container smoke:
```bash
python3 scripts/validate_host_presentation.py --include-container-smoke
```

`python3 scripts/run_public_validation.py` wraps the core of the public set and also runs the tracked-path privacy check. It is the recommended cross-platform entrypoint (a bash wrapper is also available at `artifact/run-public-validation.sh`).

## Maintainer-Only Strict Set

Maintainers with the private holdout pack should additionally run:

```bash
python3 scripts/validate_v0_release.py
python3 scripts/validate_v1_readiness.py
```

These do not publish private evidence; they enforce strict gates against
local holdout contents.

## Privacy Check

A public commit must not track private/raw artifact paths. Run:

```bash
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs harbor-jobs .harbor .handoff
```

The command must print nothing.

## Harbor Local Preflight

To check whether the local checkout is ready to attempt a future Harbor run:

```bash
python3 scripts/check_harbor_local_execution.py
```

This generates and validates a temporary public skeleton and records whether
the `harbor` CLI is on `PATH`. It does not invoke `harbor run`. In a checkout
without Harbor installed, the local execution gate is recorded as blocked on
the missing CLI.

## Harbor Local Smoke

To create a redacted local smoke summary without committing raw
`harbor-jobs/` output:

```bash
python3 scripts/run_harbor_local_smoke.py
python3 scripts/validate_harbor_local_evidence.py
```

The checked-in one-task smoke summary proves only local task/agent/verifier
execution and deliberately retains `parity_verified: false`. The separate
six-task parity artifact records current matching native/Harbor rewards:

```bash
python3 scripts/validate_harbor_parity_experiment.py
python3 scripts/validate_packaged_harbor.py
```

The first command verifies the six-of-six `per_task_pairing` artifact. The
second builds and installs the wheel outside the source tree, invokes the
packaged CLI, builds one task, and exercises the packaged scorer bridge. These
checks do not claim full 63-task/model parity or platform acceptance.

## Generated Charts And Tables

Paper and chart reproducibility:

```bash
python3 scripts/generate_benchmark_charts.py
python3 scripts/generate_paper_tables.py
git diff --exit-code -- paper/shared docs/assets/benchmark-charts
```

The diff should be empty for a release-candidate commit unless charts or
tables were intentionally refreshed.

## When A Check Fails

- `validate_public.py`: manifest, scoring, or privacy regression. Inspect
  the failure context; do not weaken validators to clear a check.
- `validate_host_presentation.py`: host-facing artifact, markdown link,
  template, or schema regression. Fix the affected host artifact; do not
  weaken validators.
- `check_claim_boundary.py`: claim-boundary wording drift. A forbidden
  phrase appeared outside an allowed negation context. Fix the wording;
  do not weaken the claim-boundary check.
- `validate_baseline_registry.py`: baseline registry drift. Refresh the
  affected baseline or update the registry contract.
- `validate_harbor_parity_experiment.py`: parity evidence drift. Refresh
  the parity evidence or correct the methodology field.
- `validate_harbor_adapter_templates.py`: adapter template drift. Refresh
  the affected template.
- `validate_v1_readiness.py --allow-incomplete --public-view
  --expected-output`: public-view fixture drift. The rendered readiness
  JSON no longer matches the expected fixture. Refresh the public-view
  fixture only if a tracked gate intentionally changed; do not weaken
  readiness truth conditions. This is not a claim of external validation.
- `git diff --check`: whitespace or conflict-marker regression.
- Privacy check: investigate the tracked file before unstaging.
