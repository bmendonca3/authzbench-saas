# Kaggle-Like Presentation To-Do List

Status: host-presentation planning checklist. This list excludes independent
external review work and does not claim platform acceptance, host operation, or
third-party submissions.

## P0 Before Sending A Host Packet

- [x] Single entrypoint: [`docs/host-review-package.md`](host-review-package.md)
- [x] Final candidate commit has passing GitHub Actions public validation run: `27598211473`
- [x] Public no-Docker validation command documented: `python3 scripts/validate_public.py --include-scripted-baseline`
- [x] Full CI/container-smoke validation command documented: `python3 scripts/validate_public.py --include-scripted-baseline --include-container-smoke`
- [x] Proposed host model recorded: Model A review package + Model B pilot path; Model C deferred
- [x] Host-facing one-page summary added: [`docs/host-facing-one-page-summary.md`](host-facing-one-page-summary.md)
- [x] Raw private holdouts and solution files excluded from public Git
- [x] Public-safe holdout counts/fingerprints documented
- [x] CSV positioned as evidence-bundle index: [`platform/kaggle/sample_submission.csv`](../platform/kaggle/sample_submission.csv)
- [x] Public dry-run bundle added: [`platform/kaggle/dry-run-bundle/`](../platform/kaggle/dry-run-bundle)
- [x] Exact host commands recorded: [`docs/host-review-walkthrough-transcript.md`](host-review-walkthrough-transcript.md)

## P1 Host-Readiness Polish

- [x] Add a generated host-review bundle script: [`scripts/build_host_review_bundle.py`](../scripts/build_host_review_bundle.py)
- [x] Add a host-review bundle manifest with file paths and SHA-256 hashes: [`scripts/validate_host_review_bundle.py`](../scripts/validate_host_review_bundle.py)
- [x] Add a rules template: [`platform/kaggle/rules-template.md`](../platform/kaggle/rules-template.md)
- [x] Add a competition page draft: [`platform/kaggle/competition-page-draft.md`](../platform/kaggle/competition-page-draft.md)
- [x] Add a sample `submission.json` bundle beside the CSV sample: [`platform/kaggle/sample_submission.json`](../platform/kaggle/sample_submission.json)
- [x] Add a validator for `platform/kaggle/sample_submission.csv`: [`scripts/validate_kaggle_sample_submission.py`](../scripts/validate_kaggle_sample_submission.py)
- [x] Add an example host-side private solution file schema, with toy data only: [`platform/kaggle/toy_solution_file.csv`](../platform/kaggle/toy_solution_file.csv)
- [x] Add a short host decision log template: [`platform/kaggle/host-decision-log.template.md`](../platform/kaggle/host-decision-log.template.md)
- [x] Add a compact baseline summary table: [`docs/host-baseline-summary.md`](host-baseline-summary.md)
- [x] Add a reproducibility matrix: [`docs/host-reproducibility-matrix.md`](host-reproducibility-matrix.md)

## P2 Nice-To-Have Before A Broader Launch

- [x] Add a one-page architecture diagram: [`docs/host-architecture.md`](host-architecture.md) (Mermaid flowchart)
- [x] Add issue templates: `.github/ISSUE_TEMPLATE/`
- [ ] Add release tags or signed release artifacts for the final host packet.
- [x] Add a citation and versioning note: [`docs/host-packet-versioning.md`](host-packet-versioning.md)
- [x] Add a maintainer runbook for rotating holdouts: [`docs/host-private-leakage-response.md`](host-private-leakage-response.md)
- [x] Add a FAQ: [`platform/kaggle/faq.md`](../platform/kaggle/faq.md)
- [x] Add a walkthrough transcript: [`docs/host-review-walkthrough-transcript.md`](host-review-walkthrough-transcript.md)

## Host Decisions Still Owned By The Host

- **Native scoring shape**: CSV-only, CSV-plus-evidence bundle, runner image, or model adapter.
- **Private data custody**: host-controlled, maintainer-operated, or staged migration.
- **Public display policy**: diagnostic public rows, private-candidate rows, or host-verified rows.
- **Rerun policy**: fixed schedule, host-requested reruns, or reruns on pack rotation only.
- **Appeal policy**: what evidence is reviewed, who decides, and what is logged.
- **Stale-score policy**: when old scores remain visible, are archived, or are marked non-comparable.

## Definition Of Presentation-Ready

The repository is presentation-ready for a Kaggle-like host discussion when a fresh clone can pass public validation, the host packet has one clear entrypoint, the sample submission story is concrete, private materials are out of public Git, the claim boundary is enforced by CI, and the host can see exactly which decisions remain theirs.
