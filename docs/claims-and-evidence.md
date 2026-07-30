# Claims and Evidence

This document serves as the canonical claim ledger and evidence matrix for AuthZBench-SaaS, outlining the repository's claims, supported evidence, approved public framing, and deferred external validation tracks.

---

## 1. Top-Level Interpretation Note

The public-view readiness fixture at
[`artifact/expected-output/v1-readiness-public-view.json`](../artifact/expected-output/v1-readiness-public-view.json)
is checked with `--allow-incomplete --public-view --expected-output`. The
fixture is a fixture-matching public-view check: `--allow-incomplete`
returns 0 when the rendered output matches the expected fixture, even if
`v1_ready` is false under honest post-cleanup evidence (for example,
release-affecting docs changed after the pinned `benchmark_source_sha`).
The fixture reports the current internal gate state and any unmet gates; a
fixture match is not a claim of external validation.

It does not assert independent external review, SaaS-provider scenario
validation, hosted leaderboard operation, or platform acceptance.
Those are deferred validation tracks. This is not hosted leaderboard operation, not platform acceptance, and not third-party submissions.

---

## 2. Canonical Claim Ledger

This ledger defines the boundary between supported claims and forbidden stronger wordings. Reviewers and contributors must adhere to this boundary across all public communications.

| Claim / Category | Status | Evidence | Forbidden Stronger Wording |
| --- | --- | --- | --- |
| **`v1.0-internal` complete** | Supported | `docs/releases/v1.0-internal.md`; public-view readiness fixture match with `--allow-incomplete`; current fixture reports `v1_ready: false` with 1 unmet gate under honest post-cleanup evidence; internal/non-external scope only | "community benchmark", "externally validated benchmark", "hosted leaderboard operation benchmark" |
| **63 public tasks** | Supported | `tasks/` manifests and public baseline summaries | "hosted leaderboard operation public split" |
| **48 private holdout tasks** | Supported by fingerprint / count | Ignored local private packs, rotation metadata, and public redaction summaries | "publicly reproducible private holdouts", "open private holdout task list" |
| **Local Harbor no-tools adapter path** | Supported with current-evidence limits | Packaged `authzbench_harbor/` CLI and isolated wheel-install smoke support `no_tools`; `live_http_tool_agent` is `planned_unsupported` and fails closed. The one-task/six-task local execution and parity artifacts are historical, and the intended three-task compatibility pilot currently requires a source-matching rebuild and rerun. | "current-source Harbor execution", "Harbor accepted", "Harbor endorsed", "Harbor leaderboard-ready", "full 63-task/model parity" |
| **Local / containerized submission smoke** | Supported | `artifact/submission-runner-smoke.json` and local test suites | "hosted leaderboard", "hosted submission operation" |
| **Deterministic backend-replay scorer** | Supported | Scorer package codebase and test suites | "human-judged scoring", "model-graded scoring" |
| **Public / private split with holdout governance** | Supported | Rotation and lifecycle specification documents | "public leaderboard operation", "open private holdout reuse" |
| **Current scripted sanity baseline** | Supported | Fresh 63-task scripted sanity baseline summaries | "current model baseline", "current tool-agent baseline" |
| **Current model / tool-agent baseline** | Supported with derivation limits | Fourteen saved full-63-task public runs were rescored offline under policy v2 without repeating model execution. Each summary hashes its source evidence and derived rows. Adapter/runner failures fail closed and affected rows are end-to-end model-plus-harness evidence, not clean model-only evidence. | "fresh policy-v2 model rerun", "all major model families", "all current frontier models", or clean model-only capability when a run records harness failures |
| **Synthetic targets only** | Supported | Sandbox applications; absence of real-SaaS API keys or integrations | "production SaaS coverage", "real customer SaaS authorization coverage" |
| **Independent external review** | Not done | Intake packet exists; no reviewer dispositions recorded | "external review complete", "industry-standard benchmark" |
| **SaaS-provider scenario validation** | Not done | Validation tracks defined; no provider endorsements recorded | "SaaS-validated", "real-world validated", "AppSec-reviewed" |
| **Hosted public leaderboard** | Not done | Design specification only; no hosted execution implemented | "hosted leaderboard-ready", "hosted leaderboard operation" |
| **Platform acceptance (Harbor/Kaggle/etc.)** | Not done | Local preflight and blocker tracking only | "Harbor accepted", "Harbor endorsed", "Kaggle accepted" |
| **Third-party submissions** | Not done | Governance policy only; submission gates closed | "open for third-party submissions", "community submission open" |
| **Externally validated v1 release** | Not done | Internal RC cut only; no external review | "v1 release-ready", "v1.0 released", "externally validated v1 release" |

---

## 3. Detailed Evidence Matrix

| Evidence | What It Proves | What It Does Not Prove |
| --- | --- | --- |
| **63-task public split** | Presence of BOLA, BFLA, and secure controls across 6 apps. | v1 release readiness or hosted leaderboard operation. |
| **Scripted sanity baseline** | Validates the public split scorer and oracle paths. | Model capability or private holdout performance. |
| **Stale baselines** | Stale runs remain auditable as historical snapshots. | Direct comparability with the current 63-task split. |
| **Promoted-composite public baselines** | When present, combine immutable prior public-split evidence with fresh reruns of exactly the newly promoted public tasks and are current only by explicit composite construction. | A fresh full rerun of every public task. |
| **Offline-rescored public baselines** | Evaluate preserved full-split submissions under the corrected scorer with fail-closed execution metadata and content-hash provenance. | Repeated model execution under the new scorer, prompt, adapter, or environment. |
| **Scorer replay** | Submitted evidence can be verified against backend behavior. | The agent interacted with a live target unless request logs are correlated. |
| **Secure controls** | The benchmark penalizes false positives and over-reporting. | All real SaaS false-positive patterns are covered. |
| **Rotation metadata** | Private packs are defined, verified, and gitignored. | Public reproducibility of the private holdouts. |
| **Local Harbor adapter and historical scoped parity** | The no-tools packaged CLI installs outside the source tree. Historical one-task and six-task public runs remain auditable, including a six-of-six empty-findings/native reward match. | Current-source compatibility until the three-task pilot is rebuilt and rerun; live HTTP support; full 63-task parity; representative model/agent parity; Harbor platform acceptance; or hosted Harbor-side operation. |

---

## 4. Approved Public Framing

Use only the approved terminology below when describing AuthZBench-SaaS.

### Approved Wording
* `released v0.0 benchmark artifact` / `v0.0 release evidence`
* `current v1-prep public split` / `v1.0-internal public-view readiness`
* `public-split baseline` / `deterministic backend replay`
* `protected private-holdout evidence`
* `boundary-vocabulary calibration`
* `v1/community submission governance specification`
* `repo-side local Harbor adapter path`
* `six-task local Harbor/native empty-findings parity`
* `offline rescore of saved public submissions under score-policy-v2`
* `public-view readiness fixture match (--allow-incomplete)`

### Avoid Wording
* `hosted leaderboard-ready`
* `validated model benchmark`
* `v1/community-scale benchmark`
* `externally validated v1 release` (use only under "Not done" status)
* `production vulnerability discovery benchmark`
* `private holdouts are publicly reproducible`
* `Harbor accepted` / `Harbor endorsed`

---

## 5. Deferred v2 Validation Tracks

External review and platform acceptance are tracked below as v2 validation gates.

### Application Security Review
* **Goal**: Independent AppSec reviewer assesses task realism, authorization boundary quality, and false-positive controls.
* **Packet**: `docs/reviews/external-review-packet.md`.
* **Criteria**: Confirm BOLA/BFLA, role, token-scope, sharing, and admin-action tasks are realistic; no unsafe/ambiguous tasks.

### Benchmark and Evals Methodology Review
* **Goal**: Independent evals reviewer evaluates task split design, scoring semantics, repeated-run evidence, and claim boundary.
* **Packet**: `docs/reviews/external-review-packet.md` and technical reports.
* **Criteria**: Verify task split and scoring semantics support stated claims without implying hosted leaderboard operation.

### AI-Agent and Tooling Review
* **Goal**: Independent agent reviewer assesses harness types, tool access, target-request correlation, and comparability keys.
* **Criteria**: Assess whether harness assumptions and agent comparability keys support fair agent-to-agent comparison.

### SaaS-Provider Scenario Validation
* **Goal**: Validation from one or more SaaS authorization providers that task scenarios and oracle logic accurately reflect real SaaS authorization patterns.

### Optional Platform Review (Kaggle and Harbor)
* **Goal**: Full Harbor adapter parity, platform publishing, and platform review.

---

## 6. Triggering v2 External Validation

1. Recruit independent reviewers for each lane.
2. Use `docs/reviews/external-review-packet.md` as the intake packet.
3. Use `docs/reviews/external-review-intake.md` as the human response form.
4. Record findings in `docs/reviews/external-review-summary.json` (real evidence only).
5. Update `docs/reviews/external-review-summary.md` to reflect completed lanes.
6. Do not mark v2 validation release complete until all three required lanes (AppSec, evals, agent/tooling) record real human decisions.

---

## 7. Generated Charts

The public baseline metrics and task mixes can be regenerated using `python3 scripts/generate_benchmark_charts.py`. They represent public-safe artifacts only and do not turn public-split scores into leaderboard-candidate rows. Leaderboard-candidate rows use local row eligibility with public-safe private-holdout metadata, inside the repo evidence model.
