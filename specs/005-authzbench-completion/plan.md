# AuthZBench-SaaS Product And Benchmark Completion Plan

## Strategy

Close the work in evidence order. First establish one auditable inventory and
fix fail-open validators/runtime paths. Then converge benchmark truth, release
artifacts, paper/claims, and review contracts. Finally run independent
post-change audits and the strongest feasible gates. External actions begin
only from a frozen, user-authorized commit.

## Phase 0 — Inventory And Safety Baseline

Owner: parent/DAD, assisted by bounded independent audit lanes.

1. Capture branch/HEAD/dirty state and preserve all existing work.
2. Reconcile release-readiness, review-contract, and benchmark-integrity audit
   findings into the task list and traceability table.
3. Prove dependency-free test discovery executes intended mutation suites.
4. Keep current 9/10 source-binding failure and all external pending gates
   honest.

Acceptance: every material finding is classified as local, external,
private-maintainer, source-freeze, or optional, with no destructive action.

## Phase 1 — Fail-Closed Contracts And Benchmark Integrity

Owner: local implementation lanes; parent verifies.

1. Harden JSON/task/oracle/fingerprint/Harbor/scorer contracts against
   duplicates, non-finite values, stale artifacts, unsupported capabilities,
   and source drift.
2. Make review validators reject unresolved/rejected/blocking evidence, bind
   all lanes and mandatory source trees to one real reviewed commit, and prove
   remediation happened after review.
3. Create a coherent pending cohort-methodology decision surface and separate
   controlled private-review schema/projection contract.
4. Add adversarial focused tests for every repaired failure mode.

Acceptance: structural pending states pass only structural checks; strict
completion remains red until real evidence exists; all known false positives
have mutation tests.

## Phase 2 — Runtime, Packaging, And Reproduction

Owner: local implementation lanes; parent verifies from a clean/materialized
source copy where feasible.

1. Repair fail-open validation/reproduction wrappers and packaging inputs.
2. Materialize host-review bundles from the exact Git ref and validate the
   materialized tree, not ambient files.
3. Align Docker context safety, package data, Python version, license,
   walkthrough, CI, host ledger, release metadata, and artifact index.
4. Run clean-install, root/container/static, and reproduction checks supported
   by the local environment.

Acceptance: a clean source copy can install and execute the canonical public
validation path; every skipped environment-dependent check has an exact reason.

## Phase 3 — Paper, Generated Artifacts, And Claims

Owner: local documentation/artifact implementation lane; parent verifies
regeneration and semantic alignment.

1. Update the paper and technical report to current 63/48/111 counts and
   offline-rescore/historical evidence truth.
2. Regenerate tables/charts/inventories from canonical data.
3. Remove contradictory “complete/current” wording and add regression checks
   across README, roadmap, status, claims, paper, host, and artifact index.
4. Compile LaTeX when the toolchain is available; otherwise preserve exact
   generation and syntax evidence and record the toolchain blocker.

Acceptance: all current surfaces agree and historical rows remain explicitly
historical.

## Phase 4 — Independent Post-Change Audit

Owner: fresh independent agents; parent owns fixes and final verdict.

1. Audit correctness/edge cases.
2. Audit security/privacy/claim boundaries.
3. Audit benchmark/artifact/reproducibility integrity.
4. Audit task/spec completeness and delegated-change accounting.
5. Fix every verified local finding and rerun affected checks.

Acceptance: no known local P0/P1 defect remains and all lower-priority residual
risk is explicitly recorded.

## Phase 5 — Kaggle Executor Parity

Owner: benchmark maintainer with Kaggle infrastructure support.

Dependency: a Kaggle-supported host/image contract that starts Harbor 0.15's
egress-control sidecar.

1. Ask Kaggle the bounded KQ-005 host/image question only after explicit
   approval to send.
2. Confirm the supported runner image digest and host capabilities.
3. Run exact source `20cd189` and the unchanged secure-control task digest.
4. Compare local and executor source, task, trajectory, CTRF, verifier, reward,
   resources, token use, and isolation behavior.

Acceptance: explained parity with complete trial evidence, or a new precise
platform blocker. A local Docker-in-Docker failure is not Kaggle-hosted
evidence.

## Phase 6 — Independent Validity And Realism

Owners: independent AppSec, benchmark/evals, agent/tooling, and SaaS/product
security reviewers.

1. Freeze a review commit and refresh the prepared packets against it.
2. Collect structured reviewer records with dates, reviewed artifacts,
   findings/no-findings, dispositions, decisions, and claim-boundary impact.
3. Resolve blocking findings locally and repeat only affected checks.
4. Mark a lane complete only when its validator accepts a real reviewer record.

Acceptance: all four validity lanes have direct dispositions and no unresolved
blocking finding.

## Phase 7 — Hosted Operation And Launch

Owners: benchmark maintainer and Kaggle.

1. Name a backup maintainer and maintenance/rollback policy.
2. Obtain organization approval and finalize the private synchronization and
   privacy model.
3. Exercise hosted submission/leaderboard operation with protected holdouts.
4. Approve launch tier, date, technical summary, messaging, and assets.
5. Record publication and leaderboard URLs and run the final claim review.

Acceptance: organization, privacy, hosted operation, ownership, launch, and
publication evidence are each independently observable.

## Separate Optional Lane — OpenAI Matrix

Resume `specs/001-openai-model-effort-matrix/T016` only with separate authority
after the hosted-credit sentinel is absent. Preserve the one complete row and
23 incomplete rows; do not rerun completed admission merely to show activity.
This lane is useful comparative evidence but is not on the Kaggle launch
critical path.

## Verification

Fast loop:

```bash
python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view
python3 scripts/check_claim_boundary.py
python3 scripts/check_markdown_links.py
git diff --check
```

Strong local gate:

```bash
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/validate_v2_external_validation.py
python3 scripts/validate_v1_readiness.py --allow-incomplete --public-view \
  --expected-output artifact/expected-output/v1-readiness-public-view.json
```

Release-candidate loop additionally requires clean/source-materialized install
and reproduction checks plus generated paper/artifact drift checks. The strict
external-review gate, exact-head source-freeze evidence, Kaggle executor
evidence, and hosted launch checks remain intentionally unavailable until their
owners act.
