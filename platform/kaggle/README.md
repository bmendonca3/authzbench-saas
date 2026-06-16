# Kaggle-Like Host Review Artifacts

This directory contains public-safe artifacts for a Kaggle or Kaggle-like host
review. It is not a platform upload and does not claim platform acceptance,
hosted operation, or external validation.

## Files

- `sample_submission.csv`: toy CSV showing the participant-facing `Id` shape
  and a pointer to evidence files. It uses public task IDs only.

## Proposed Participant Artifact

AuthZBench-SaaS does not naturally reduce to a label-only CSV. A useful
participant artifact should include:

- a CSV or manifest keyed by `Id`;
- one evidence bundle per attempted task;
- per-task `submission.json`;
- per-task request/response proof when the harness supports it;
- agent/model metadata;
- a generated `summary.json` for the run.

The CSV is best treated as an index into a structured evidence bundle. The
scorer and leaderboard validator remain authoritative.

## Sample Submission Columns

| Column | Meaning |
| --- | --- |
| `Id` | Public task ID |
| `finding_path` | Relative path to the participant's per-task `submission.json` |
| `notes` | Optional participant note; ignored by scorer unless a host adapter chooses otherwise |

## Validation Path

For the current repo package, run:

```bash
python3 scripts/validate_public.py --include-scripted-baseline
```

Future host adapters should add a targeted validator for this directory once
the host chooses CSV-only, evidence-bundle, runner-image, or model-adapter
submission.

## Private Holdout Handling

Private holdouts are not included here. A host-controlled solution file should
be generated outside public Git from protected private packs and referenced only
by version, hash, and public-safe fingerprint in published summaries.

