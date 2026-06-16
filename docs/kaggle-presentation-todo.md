# Kaggle-Like Presentation To-Do List

Status: host-presentation planning checklist. This list excludes independent
external review work and does not claim platform acceptance, host operation, or
third-party submissions.

## P0 Before Sending A Host Packet

- Keep [`docs/host-review-package.md`](host-review-package.md) as the single
  entrypoint for a host or reviewer.
- Confirm the final candidate commit has a passing GitHub Actions public
  validation run.
- Confirm `python3 scripts/validate_public.py --include-scripted-baseline`
  passes from a clean checkout.
- Decide which host model is being proposed first:
  repo-side dataset review, maintainer-operated private evaluation, or native
  CSV-plus-evidence scoring.
- Write the host-facing one-page summary from the claim boundary, not from
  aspiration language.
- Keep raw private holdout manifests and solution files outside public Git.
- Publish only public-safe holdout counts, versions, hashes, and fingerprints.
- Use [`platform/kaggle/sample_submission.csv`](../platform/kaggle/sample_submission.csv)
  only as a sample index into evidence bundles.
- Prepare a small public dry-run bundle that shows one vulnerable task, one
  denial control, and one authorized-allow control.
- Record the exact commands a host should run to reproduce public validation.

## P1 Host-Readiness Polish

- Add a generated host-review bundle script that copies only public-safe files
  into a zip or directory.
- Add a host-review bundle manifest with file paths, SHA-256 hashes, and
  claim-boundary notes.
- Add a `platform/kaggle/rules-template.md` draft that explains participant
  submissions, evidence-bundle expectations, allowed automation, and privacy
  boundaries.
- Add a `platform/kaggle/competition-page-draft.md` with title, overview,
  evaluation, data, submission format, and limitations sections.
- Add a sample `submission.json` bundle beside the CSV sample.
- Add a validator for `platform/kaggle/sample_submission.csv` once the host
  model is chosen.
- Add an example host-side private solution file schema, with toy data only.
- Add a short host decision log template for private pack custody, reruns,
  appeals, score invalidation, and pack rotation.
- Add a compact baseline summary table for public split model families.
- Add a reproducibility matrix showing local public validation, CI validation,
  container smoke status, private-holdout custody status, and host decisions.

## P2 Nice-To-Have Before A Broader Launch

- Add a one-page architecture diagram for tasks, submissions, evidence bundles,
  scorer, public artifacts, and host-controlled private inputs.
- Add issue templates for host questions, packaging blockers, scoring-contract
  changes, and claim-boundary wording changes.
- Add release tags or signed release artifacts for the final host packet.
- Add a citation and versioning note specific to the host packet.
- Add a maintainer runbook for rotating holdouts after any public leakage.
- Add a short FAQ for why a label-only CSV is not enough for this benchmark.
- Add a minimal walkthrough video or transcript for a host reviewer running the
  public validation command.

## Current Open Host Decisions

- Native scoring shape: CSV-only, CSV-plus-evidence bundle, runner image, or
  model adapter.
- Private data custody: host-controlled, maintainer-operated, or staged
  migration.
- Public display policy: diagnostic public rows, private-candidate rows, or
  host-verified rows.
- Rerun policy: fixed schedule, host-requested reruns, or reruns on pack
  rotation only.
- Appeal policy: what evidence is reviewed, who decides, and what is logged.
- Stale-score policy: when old scores remain visible, are archived, or are
  marked non-comparable.

## Definition Of Presentation-Ready

The repository is presentation-ready for a Kaggle-like host discussion when a
fresh clone can pass public validation, the host packet has one clear entrypoint,
the sample submission story is concrete, private materials are out of public
Git, the claim boundary is enforced by CI, and the host can see exactly which
decisions remain theirs.
