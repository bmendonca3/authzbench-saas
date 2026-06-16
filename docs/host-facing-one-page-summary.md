# AuthZBench-SaaS Host Review Summary

Status: Host-review package candidate. Not platform accepted, not hosted, not externally validated.

## What It Evaluates
AuthZBench-SaaS evaluates whether AI agents can prove SaaS authorization failures with backend-replayable evidence while avoiding false reports on secure controls. The benchmark uses synthetic SaaS targets with live HTTP endpoints to verify the validity of generated exploit traces.

## Current Public Artifact
- **Public Target Apps**: 6 synthetic SaaS applications running locally.
- **Public Tasks**: 60 total, with 24 vulnerable tasks and 36 secure controls.
- **Controls Mix**: 21 denial controls and 15 authorized-allow controls.
- **Validation**: Public validation, claim-boundary checks, and Docker/container smoke are required on the final candidate commit before sending a host packet. The current verified commit and run ID are recorded in `docs/host-reproducibility-matrix.md`.

## Private-Holdout Design
- **Custody**: 48 private holdout tasks are summarized publicly only by count, version, and fingerprint.
- **Privacy Boundary**: Raw private task manifests, routes, seeds, and oracle strings are gitignored and kept outside public Git to prevent participant memorization.

## Proposed Host Path
- **Model A (Review Package)**: This package serves as an initial methodology, task quality, and local reproducibility review.
- **Model B (Scoring Pilot)**: Evaluation is run via maintainer or host-controlled private runners executing submitted evidence bundles against private holdouts.
- **Model C (Native CSV Scoring)**: Deferred for this package. CSV functions as a submission index mapping to evidence bundles rather than standalone labels.

## What Participants Submit
- A CSV or JSON index listing attempted task IDs and relative paths to their corresponding evidence files.
- An evidence/findings bundle containing the exploit proof, targeted HTTP requests, boundary reasoning, and metadata.

## What the Scorer Verifies
- Exploit proof and correct backend replay.
- Correct rejection/replay of secure controls (denial & authorized-allow).
- Boundary reasoning accuracy.
- Target request coverage rate.
- Rate of invalid or malformed submissions.

## Explicit Non-Claims
AuthZBench-SaaS does not claim platform acceptance, hosted public leaderboard operation, external validation, SaaS-provider validation, or third-party submissions.
