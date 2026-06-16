# Kaggle-Like Host FAQ

## Why not just submit labels in a CSV?
Because AuthZBench-SaaS rewards backend-replayable authorization proof and penalizes false reports on secure controls. A label-only CSV cannot show whether the agent actually touched the target backend, generated replayable evidence, respected scope, or avoided over-reporting secure controls.

## How is gaming prevented?
- **Redacted Summaries**: Only count-level and fingerprint details of the private holdouts are ever made public.
- **Evidence Replay**: Submissions are validated by replaying the participant's exact HTTP requests against a private SaaS backend instance to verify the exploit proof was generated dynamically.
- **Strict Controls Penalties**: Submissions that claim exploits on secure controls (denial or authorized-allow controls) fail validation or receive heavy scoring penalties.

## What is the proposed hosting model?
We propose **Model A** (reviewing the dataset, schemas, and validators locally) plus **Model B** (maintainer-operated or host-controlled private evaluation pilot) as the initial steps. **Model C** (native platform-side CSV scoring) is deferred.
