# v1 Community Submission Governance

Status: governance specification for future v1/community operation. This
document defines the intended process; it does not claim that hosted
infrastructure or community submissions are already live.

## Claim Boundary

AuthZBench-SaaS can accept public diagnostic artifacts today, but it is not
leaderboard-ready until private-holdout evaluation is operated through either:

- a maintainer-hosted runner with protected private packs; or
- a fully containerized submission path where submitters provide agent code or
  a locked runner image and maintainers execute it against private packs.

Public-split runs are useful for debugging, paper evidence, and reproducibility.
They are not eligible for release-facing leaderboard rows.

## Roles

| Role | Responsibility |
| --- | --- |
| Maintainer | Owns private packs, runner image versions, validation, row acceptance, and retirement decisions. |
| Submitter | Provides agent metadata, model/tool-access details, run bundle or runner image, and reproducibility notes. |
| Reviewer | Checks task quality, scoring validity, artifact completeness, and claim wording. |
| Release owner | Freezes score-policy, evidence-contract, benchmark fingerprint, and active private-pack version for a release. |

## Submission States

| State | Meaning |
| --- | --- |
| `received` | Bundle or runner image was received but not validated. |
| `schema_valid` | Submitted metadata passes public schema validation but is not eligible yet. |
| `needs_rerun` | Bundle is structurally useful but uses stale tasks, stale scoring, missing provenance, or an incompatible fingerprint. |
| `private_eval_queued` | Maintainer accepted the run for protected private evaluation. |
| `eligible_candidate` | Private-holdout row passed evidence, false-positive, provenance, and policy gates. |
| `accepted` | Row is published under the current private-pack and score-policy versions. |
| `legacy_snapshot` | Row remains historical after a pack, task, or score-policy rotation. |
| `deprecated` | Row should not be used because leakage, runner error, scorer bug, or provenance failure changed its validity. |
| `rejected` | Row failed required policy, safety, provenance, or evidence gates. |

## Eligibility Gates

A v1 leaderboard candidate must satisfy all gates below:

1. The evaluation split is a private holdout, not the public split.
2. The runner emits the benchmark fingerprint and comparability key.
3. The row uses the current `leaderboard-submission-v1` schema or a declared
   successor.
4. The row declares score-policy, evidence-contract, benchmark commit SHA,
   private-pack version, harness type, model label, tool access, timeout, retry,
   and runner image or command provenance.
5. Repeated-run provenance is present for leaderboard rows, with source
   summaries and a primary run.
6. False-positive and invalid-submission counts are reported separately from
   exploit-proof success.
7. Live HTTP tool-agent rows include target-request coverage when the harness
   permits it.
8. Protected execution evidence shows that public submitter code could not read
   private manifests, raw private results, captures, panel logs, credentials, or
   unrelated local data.
9. No private task IDs, bodies, seeds, routes, or raw per-task private outcomes
   appear in the public artifact.
10. The row survives maintainer review and any required external reviewer
    challenge for the active release.

## Hosted Runner Path

The public-safe executable procedure checklist is tracked at
`artifact/hosted-submission-execution-runbook.json`. It is runbook evidence
only, not release-candidate smoke evidence.

The hosted path should operate like this:

1. Maintainers freeze the active private pack and runner image.
2. Submitters provide a model endpoint configuration or agent adapter with
   declared tool access.
3. The hosted runner executes the agent in an isolated environment with no
   private-pack read access except through benchmark APIs.
4. The scorer writes raw private results to an ignored protected evidence root.
5. A redacted summary and candidate leaderboard row are generated.
6. Validation recomputes aggregate metrics from source summaries.
7. Maintainers review the row, publish only public-safe metadata, and archive
   raw private evidence outside public Git.

## Fully Containerized Path

The containerized path should operate like this:

1. Submitters provide a runner image or build recipe pinned by digest.
2. Maintainers run the image with network, filesystem, process, and timeout
   limits appropriate to the benchmark policy.
3. Private holdout manifests are mounted only into a scorer-controlled process,
   not the submitter process.
4. The submitter process interacts with targets through the intended benchmark
   interface.
5. The same summary, validation, redaction, and publication gates as the hosted
   path apply.

This path is acceptable for v1 only after the isolation model is tested on the
maintainer platform and documented with a reproducible smoke check.

The executable smoke entrypoint is:

```bash
python3 scripts/containerized_submission_smoke.py \
  --private-pack tasks_private/holdout/<active-pack> \
  --output artifact/submission-runner-smoke.json \
  --benchmark-source-sha <benchmark-source-sha> \
  --private-pack-version <active-pack-version> \
  --execution-scope release_candidate
```

Public CI runs the same isolation mechanism with an ephemeral rehearsal pack.
That rehearsal verifies container constraints, rendered-context-only mounting,
private-manifest read denial, scorer-controlled evaluation, cleanup, and
public-output redaction. It cannot satisfy the release gate because the emitted
scope is `rehearsal`, not `release_candidate`.

## Rotating Private Packs

Private packs follow `docs/holdout-rotation-protocol.md`.

The public-safe operation checklist is tracked at
`artifact/private-holdout-operation-runbook.json`. It is runbook evidence only,
not private holdout evidence.

For community operation, each release must declare:

- active private-pack version;
- shadow private-pack version, if any;
- score-policy version;
- evidence-contract version;
- benchmark fingerprint;
- pack compatibility statement;
- retirement date or next review trigger.

When a pack rotates, older accepted rows become `legacy_snapshot` unless the
release owner explicitly declares compatibility and reruns required core
baselines.

## Reruns, Ties, And Stale Scores

- Any task-body, task-count, score-policy, evidence-contract, or private-pack
  change makes previous rows stale for current comparison unless compatibility
  is explicitly declared.
- Ties should be broken only by declared secondary metrics, such as lower
  false-positive rate, higher boundary-reasoning pass rate, lower invalid
  submission rate, and then fewer tool probes or lower runtime if those are
  recorded consistently.
- Submitters may request reruns when infrastructure errors are documented.
  Model-output variance alone should be handled through repeated-run policy,
  not ad hoc cherry-picking.
- A row with a better `mean_score` but worse false-positive behavior should not
  be described as strictly better without the metric tradeoff.

## Attestation

A reviewable run bundle should follow `artifact/run-bundle.md`. For v1, the
attestable bundle should additionally include:

- submitter identity or organization handle;
- runner image digest or hosted runner version;
- private-pack version, redacted to version only;
- benchmark fingerprint;
- comparability key;
- source-summary hashes;
- repeated-run source IDs;
- maintainer validation timestamp;
- reviewer decision status;
- declaration that no private artifacts are included in public output.

Signing can be added later, but unsigned bundles must still be hash-addressable
and tied to immutable source summaries.

## Appeals And Deprecation

Maintainers should accept appeals only for:

- infrastructure failures;
- documented runner misconfiguration;
- scorer bug;
- private-pack flaw;
- row metadata or attribution error.

Appeals should not reveal private tasks. If an appeal identifies a real scoring
or task issue, affected rows should be marked `deprecated` or `legacy_snapshot`
with a public-safe explanation.

## Minimum v1 Launch Bar

Before calling the benchmark v1/community-ready, maintainers need:

- at least one active and one candidate or shadow private pack;
- protected private execution on the intended maintainer platform;
- repeated no-tools and tool-agent private-holdout baselines;
- public validation and privacy scans passing on the release commit;
- external AppSec, benchmark/evals, and AI-agent/tooling review dispositions;
- a documented hosted or fully containerized submission path with a passing
  smoke check;
- a public row publication policy that separates accepted, stale, legacy, and
  deprecated rows.

The final report and IEEE scaffold refresh procedure is tracked in
`artifact/v1-paper-readiness-runbook.json`. That file is a checklist for
claim-boundary, table, chart, LaTeX, and publication-rule checks; it is not
release-candidate paper readiness evidence.

The final release-candidate validation procedure is tracked in
`artifact/v1-release-candidate-validation-runbook.json`. That file is a
checklist for collecting external release evidence; it is not release evidence
and does not make the repository v1/community-ready.

Until then, repository submissions and public runs should be labeled diagnostic
evidence only.
