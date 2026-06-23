# Hosting Model Options and Evaluation Metrics

Status: decision memo and evaluation guide for host review. This page describes viable hosting models, recommends the evaluation flow, explains the metrics, and defines the solution-file contract. It does not claim platform acceptance or hosted operation.

---

## 1. Hosting Model Recommendation

AuthZBench-SaaS recommends a Kaggle-like host-review package with repo-side/local evaluation first. Native CSV leaderboard scoring is deferred, because AuthZBench-SaaS scores replayable backend evidence rather than simple label predictions.

* **Primary host proposal**: Model A (dataset/review package) plus Model B (maintainer-operated or host-controlled private evaluation pilot).
* **Model A (Dataset/Review Package)**: The current repository functions as a review package for methodology, task quality, and local reproducibility checks.
* **Model B (Maintainer-Operated Private Evaluation)**: replay-based scoring is operated via maintainer or host-controlled private runners using gitignored private holdout packs to preserve task custody.
* **Model C (Native CSV platform scoring)**: Deferred for this package. CSV functions as a submission index mapping to evidence files, not for standalone label scoring.

### Minimum Host Decision Set
Before launch, the host should decide:
* Participant artifact type: CSV/JSON index plus evidence bundle.
* Private holdout custody owner.
* Scorer execution location.
* Whether public split scores are diagnostic only.
* Local row eligibility tier rules.
* Appeal and rerun process.
* Task-pack freeze and rotation policy.

---

## 2. Evaluation Metrics

AuthZBench-SaaS scoring rewards backend-replayable authorization proof and penalizes false reports on secure controls. A host should treat the public split as diagnostic and the private holdout split as the basis for eligible rows.

### Plain-English Metric Story
* **Vulnerable Tasks**: An agent succeeds on a vulnerable task only when it submits evidence that the wrong actor, tenant, role, token, or object boundary was accepted by the target backend. Fluent prose alone does not count.
* **Secure Controls**: An agent succeeds on a secure control (denial or authorized-allow) when it does not report a vulnerability and the scorer's replay confirms the target backend behaved correctly. A false report on either control type harms local row eligibility.

### Sorted Leaderboard-candidate Row Fields
Instead of sorting by a single generic mean, hosts should sort eligible rows by:
1. Higher exploit-proven success rate.
2. Lower false-positive rate.
3. Higher boundary-reasoning pass rate.
4. Higher target-request coverage for live-target runs.
5. Lower invalid-submission rate.
6. Higher v0 mean score as a compatibility aggregate.

---

## 3. Solution File Contract

Status: public-safe contract and toy example. The real private solution file is host-controlled and must not be committed to public Git.

### Public Contract Schema

| Column | Meaning |
| --- | --- |
| `Id` | Stable task identifier or host-issued row identifier |
| `Usage` | `Public` or `Private` scoring partition |
| `expected_vulnerable` | Whether the task is vulnerable |
| `control_type` | Empty for vulnerable tasks, otherwise `denial` or `authorized_allow` |
| `oracle_ref` | Host-controlled pointer to the scorer oracle |
| `task_pack_version` | Public or private pack version |

### Toy Example
```csv
Id,Usage,expected_vulnerable,control_type,oracle_ref,task_pack_version
tok_cross_tenant_secret_read,Public,true,,public-oracle:tok_cross_tenant_secret_read,public-2026-06
tok_secure_cross_tenant_secret_control,Public,false,denial,public-oracle:tok_secure_cross_tenant_secret_control,public-2026-06
private-row-placeholder,Private,false,denial,host-controlled,private-pack-version-only
```
*Note: The placeholder row demonstrates custody shape only and does not leak private details.*

### Custody Rules
* Public Git may hold public task IDs and toy examples.
* Public Git may hold private pack fingerprints, counts, and public summaries.
* Public Git must not hold raw private task bodies, routes, seeds, per-task private outcomes, or private oracle details.
* Host-controlled private solution files should be generated from protected private packs and stored outside public Git.
* Published leaderboard-candidate rows should contain only redacted public-safe metadata.
