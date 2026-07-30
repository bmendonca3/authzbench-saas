# Execute Now: AuthZBench Phase 0 Documentation Repair

Do not ask a question and do not return another analysis-only response. The
parent/DAD has already made the decision and explicitly authorizes these three
local edits. Use the file-edit tool now, then run the checks and report.

Repository: `<canonical-checkout>`
Branch/HEAD: `main` at
`acb6434c4bb25cce53a1a9f4eb31c869986743ca`

Only edit:

1. `docs/status.md`
2. `ROADMAP.md`
3. `tests/test_v1_ready_doc_alignment.py`

Required exact outcome:

- Change the status date to `2026-07-28`.
- Near the opening of `docs/status.md`, state concisely that:
  - the completed `v1.0-internal` label describes a historical
    internal/non-external snapshot;
  - current `main` is not a freshly validated release candidate;
  - at audited HEAD `acb6434`, public-view readiness is 9/10 and
    `paper_and_artifact_readiness` correctly remains false because
    release-affecting changes followed source pin `54e87b0`;
  - the old smoke/private-row/paper/CI records remain historical evidence, not
    current-HEAD evidence; and
  - a new candidate requires a deliberate source freeze plus fresh matching
    smoke, private rows, paper tables/charts/LaTeX, fixture, and CI/release
    evidence. Keep external/Kaggle/launch gates separate.
- In `ROADMAP.md`, preserve Milestone 5 as a historical completed snapshot but
  change its heading/status text so it cannot be read as current-HEAD
  readiness. Add an unchecked `Current-head evidence refresh` subsection with
  the source-freeze and fresh-evidence dependency above.
- In `tests/test_v1_ready_doc_alignment.py`, add one focused regression test
  that reads `docs/status.md` and `ROADMAP.md` and asserts durable semantic
  phrases establishing:
  - historical snapshot versus current `main`;
  - current public-view `9/10`;
  - an open current-head evidence refresh.
  Do not assert the transient count of changed files.

Do not edit the validator, evidence JSON, expected fixture, source SHA,
allowlists, benchmark/scorer/baseline files, or any completion packet. Do not
commit or push. Do not delegate.

Run:

```text
python3 -m pytest -q tests/test_v1_ready_doc_alignment.py
python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view --expected-output artifact/expected-output/v1-readiness-public-view.json
python3 scripts/check_claim_boundary.py
python3 scripts/check_markdown_links.py
git diff --check
```

The readiness fixture must remain honestly incomplete at 9/10. Before
returning, inspect the full diff and confirm only the three allowed tracked
files changed. Return changed files and exact check results.
