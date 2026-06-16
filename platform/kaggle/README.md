# Kaggle-Like Host Review Artifacts

This directory contains public-safe artifacts for a Kaggle or Kaggle-like host review. It is not a platform upload and does not claim platform acceptance, hosted operation, or external validation.

## Packet Decision

This packet proposes Model A review package plus Model B maintainer/host-operated private evaluation pilot. Model C native CSV-only scoring is deferred. CSV files in this directory are index/shape examples, not standalone label-scoring claims.

## Files

- `README.md`: This file.
- `sample_submission.csv`: Toy CSV showing the participant-facing `Id` shape and a pointer to evidence files. It uses public task IDs only.
- `sample_submission.json`: Toy JSON manifest that indexes the submissions directory.
- `dry-run-bundle/`: Directory containing a public dry-run bundle structure (manifest, CSV index, mock task submissions, and shape specifications).
- `toy_solution_file.csv`: Sample host-side private solution file schema with public task IDs and a private placeholder row.
- `toy_solution_file.README.md`: Explanation of the solution file columns.
- `rules-template.md`: Draft rules template for host review.
- `competition-page-draft.md`: Draft competition overview and evaluation structure.
- `host-decision-log.template.md`: Template for host operational decisions.
- `faq.md`: FAQ answering key architectural questions (e.g. why label-only CSV is insufficient).

## Participant Artifact Shape

AuthZBench-SaaS does not naturally reduce to a label-only CSV. A participant artifact includes:
- a CSV or manifest keyed by `Id`;
- one evidence bundle per attempted task;
- per-task `submission.json`;
- per-task request/response proof when the harness supports it;
- agent/model metadata;
- a generated `summary.json` for the run.

The CSV is treated as an index into a structured evidence bundle. The scorer and leaderboard validator remain authoritative.

## Sample Submission Columns

| Column | Meaning |
| --- | --- |
| `Id` | Public task ID |
| `finding_path` | Relative path to the participant's per-task `submission.json` |
| `notes` | Optional participant note; ignored by scorer |

## Validation Path

To validate these artifacts and schemas, run the host-presentation validation commands:

```bash
# Verify the sample CSV schema
python3 scripts/validate_kaggle_sample_submission.py

# Verify the dry-run bundle integrity and contents
python3 scripts/validate_kaggle_dry_run_bundle.py

# Verify the toy solution file schema
python3 scripts/validate_kaggle_toy_solution_file.py

# Run the aggregate host-presentation suite
python3 scripts/validate_host_presentation.py
```

## Private Holdout Handling

Private holdouts are not included here. A host-controlled solution file should be generated outside public Git from protected private packs and referenced only by version, hash, and public-safe fingerprint in published summaries.
