# Kaggle-Like Hosting Model Decision Memo

Status: decision memo for host review. This page describes viable hosting
models and recommends the smallest truthful path. It does not claim platform
acceptance or hosted operation.

## Recommendation

Use a Kaggle-like host-review package with repo-side/local evaluation first.
Treat native CSV leaderboard scoring as a later host decision, because
AuthZBench-SaaS scores replayable backend evidence rather than a simple label
prediction.

Recommended near-term model:

1. Publish the repo, public task pack, validation commands, and sample
   submission contract.
2. Let participants run the public split locally for diagnostics.
3. Let maintainers or the host run private-holdout evaluation in a protected
   environment.
4. Publish only schema-valid, redacted leaderboard rows after validation.

## Model A: Dataset-Only / Review Package

The host receives a benchmark artifact, documentation, sample submission, and
public validation commands. No leaderboard runs on the platform.

Use when the goal is methodology review, reproducibility review, or dataset
listing.

Pros:

- Lowest platform integration risk.
- Preserves private holdout custody.
- Fits the current repo with minimal extra implementation.

Cons:

- No live participant leaderboard.
- Host still needs a separate workflow for accepted rows.

## Model B: Maintainer-Operated Private Evaluation

Participants submit a bundle, runner image, or model adapter. Maintainers or a
host-controlled runner execute it against private holdouts and publish redacted
leaderboard rows.

Use when private anti-gaming protection matters more than native platform
automation.

Pros:

- Matches the current private-holdout design.
- Supports replay-based scoring and target-request evidence.
- Keeps raw private manifests out of public artifacts.

Cons:

- Requires operational custody and queue management.
- Requires host/maintainer policy for reruns, disputes, and stale rows.

## Model C: Native CSV-Style Platform Scoring

Participants upload a CSV keyed by task `Id`. The platform compares submitted
values to a solution file and computes a public/private score.

Use only if the competition is simplified to structured result rows or if a
platform-side evaluator can execute the richer scorer.

Pros:

- Familiar to many Kaggle participants.
- Easy sample-submission and solution-file story.

Cons:

- Does not naturally capture replayable backend proof.
- Risks rewarding guessed labels unless evidence bundle validation remains in
  the loop.
- Needs an adapter that maps evidence JSON into platform-scored fields.

## Minimum Host Decision Set

Before launch, the host should decide:

- participant artifact type: CSV, result bundle, runner image, or model adapter;
- private holdout custody owner;
- scorer execution location;
- whether public split scores are diagnostic only;
- leaderboard eligibility tier rules;
- appeal and rerun process;
- task-pack freeze and rotation policy.

## Claim-Safe Summary

AuthZBench-SaaS is ready for a Kaggle-like host-review conversation. It is not
claiming platform acceptance, hosted leaderboard operation, or native Kaggle CSV
compatibility. The recommended next step is a host review of Model A and Model B
before deciding whether Model C is worth simplifying around.

