# Privacy And Holdout Custody

AuthZBench-SaaS separates public diagnostic tasks from maintainer-private
holdouts. This is a benchmark integrity feature, not a missing artifact.

## Public Artifacts

Public artifacts may include:

- public task manifests under `tasks/`;
- synthetic local target apps under `apps/`;
- public validation scripts and expected outputs;
- public-safe aggregate private summaries;
- private pack counts and fingerprints;
- sample submission and schema examples.

## Non-Public Artifacts

Public artifacts must not include:

- raw private holdout manifests;
- raw private per-task results;
- private routes, seeds, object IDs, or oracle details;
- credentials, tokens, cookies, or local private paths;
- private panel logs or raw captures.

## Host Custody Model

A host or maintainer operating private evaluation should:

1. freeze an active private pack version;
2. keep raw private manifests outside public Git;
3. execute submitter code or submitted bundles in a restricted environment;
4. let only scorer-controlled code read private oracles;
5. publish redacted summaries and accepted leaderboard rows only after
   validation;
6. rotate packs when leakage, scorer bugs, or task-policy changes require it.

## Public Summary Boundary

Private public summaries may state counts, fingerprints, aggregate metrics, and
status labels. They should never reveal per-task private prompts, routes, seeds,
or expected outcomes.

## Review Checklist

- `git ls-files tasks_private/holdout results captures docs/reviews/panel-logs harbor-jobs .harbor .handoff`
  prints no raw private paths for public commits.
- `python3 scripts/validate_public.py --include-scripted-baseline` passes.
- Host-controlled private artifacts are referenced by version and fingerprint,
  not by raw path or contents.
- Any public leaderboard row traces back to redacted source summaries, not raw
  private evidence.

