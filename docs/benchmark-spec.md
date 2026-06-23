# Benchmark Specification

AuthZBench-SaaS measures a specific capability: whether an AI security agent can prove SaaS authorization boundary failures using backend-replayable evidence while avoiding reporting secure controls.

---

## 1. Scope and Intended Use

### Name
AuthZBench-SaaS (Authorization Benchmark for Software-as-a-Service).

### Current Status
* `v1.0-internal` release-candidate infrastructure validated.
* The public split is useful for local integration, methodology review, and baseline comparison.
* External reviews, SaaS-provider validation, and hosted leaderboard operation are tracked as v2 gates in [claims-and-evidence.md](claims-and-evidence.md). Hosted leaderboard operation, platform acceptance, and third-party submissions are not claimed and are deferred to v2 external validation.

### Intended Users
* **Security researchers** evaluating AI agent security capabilities.
* **Agent builders** testing security harnesses and boundary-enforcement models.
* **Application security teams** interested in access-control proof quality.
* **Benchmark designers** studying false-positive controls and replay scoring.

---

## 2. What It Measures & What It Does Not Measure

### What It Measures
* **BOLA and BFLA-style authorization failures** across synthetic SaaS backends.
* **Access boundaries** including tenant, organization, project, object, role, and API token scopes.
* **Replayable HTTP-style proof** demonstrating unauthorized access.
* **Correct boundary reasoning** (attacker, victim tenant, and required role).
* **False-positive avoidance** on secure controls.
* **Safe execution** within an isolated vulnerable local target.

### What It Does Not Measure
* General cyber exploitation capability.
* Exploit development against real CVEs or binary targets.
* Cloud infrastructure exploitation.
* Phishing, credential stuffing, or social engineering.
* Production SaaS target vulnerability discovery.
* Narrative report writing quality independent of technical proof.

---

## 3. Benchmark Thesis & Methodology

Most security agent benchmarks measure exploit success against CVEs or capture-the-flag (CTF) environments. AuthZBench-SaaS focuses on logical access control bugs that require multi-actor and multi-tenant reasoning:
1. **Which actor** is making the request?
2. **Which tenant, organization, or project** owns the target resource?
3. **Which role or token scope** should be required?
4. **Is the behavior a bug**, or is it authorized product behavior?

### Contamination Resistance
Each task uses a unique seed. Target SaaS apps derive tenant IDs, object IDs, and actor tokens dynamically from that seed. Public tasks render concrete values per run while keeping manifests readable and reducing hardcoded-solution value.

---

## 4. Task Types & Taxonomy

For details on current public task classifications, counts, and per-task details, refer to the generated [Task Taxonomy Matrix](task-taxonomy.md).

### Task Types
* **BOLA (Broken Object Level Authorization)**: Cross-tenant object read/write succeeds. Expected output: one finding with replayable proof.
* **BFLA (Broken Function Level Authorization)**: A lower-privileged role accesses an admin-only or restricted function. Expected output: one finding with replayable proof.
* **Secure Control (Denial)**: The backend correctly denies unauthorized access. Expected output: `findings: []`.
* **Secure Control (Authorized-Allow)**: The backend correctly allows authorized access. Expected output: `findings: []`.

### Dynamic Oracles
Every task has a machine-verifiable oracle. 
* **Vulnerable Tasks**: Submitted evidence must replay against the seeded backend and return the expected status and response subset. If a task has `evidence_requirements` (multi-step), each required step must match the request/response shape. Vulnerable tasks also declare an `expected_boundary` (attacker, victim tenant/org, and required role) which the agent must correctly identify.
* **Secure Controls**: The submission must contain no findings, and the control request must return the expected status and response subset. Secure-control manifests include `control_type` so result summaries separate denial controls from authorized-allow controls, preventing agents from getting high scores by simply reporting everything as secure.

---

## 5. Holdout and Contamination Prevention

AuthZBench-SaaS uses a strict public/private split to prevent frontier models and agent harnesses from memorizing task details.

### Public Split
The current public split is 63 public tasks tracked under `tasks/*/*.json`
manifests. Used for local smoke tests, harness integration, baseline
debugging, and public methodology review.

### Private Holdout Split
Lives entirely outside the public Git history. Private holdout manifests use the same schema but do not publish task seeds, exact routes, vulnerability locations, scorer oracle details, or reference exploits.
* The current maintainer-private holdout is 48 maintainer-private holdout tasks, summarized only through a public-safe summary with public-safe count and fingerprint metadata.
* Total public + private task scale: 111 total.
* Ignored by Git under `tasks_private/holdout/`.
* Evaluated locally via `python3 scripts/validate_holdout_pack.py`.

### Holdout Governance and Local Row Eligibility
The following governance requirements maintain maintainer-private scoring governance for leaderboard-candidate rows inside the repo evidence model.
This is repo-side local row eligibility and comparability policy, not hosted leaderboard operation. Platform acceptance, third-party submissions, and hosted leaderboard operation are not claimed and are deferred to v2 external validation.
1. **Active and Shadow Packs**: Must exist under the gitignored holdout root and report `leaderboard_suitable: true` before claiming private evidence.
2. **Rotation Metadata**: Written only in the holdout root, matching validated pack fingerprints, and never tracked in public Git.
3. **Protected Execution Summaries**: Redacted source summaries must record `host_private_paths_denied`, share a fingerprint with the active pack, and reach `run_count >= 2`.
4. **Eligible Leaderboard-Candidate Rows**: Public files list counts and blockers only; synthetic private rows are forbidden. Eligible rows must link to the active pack fingerprint.

### Holdout Execution Models
These models describe future v2 hosted-operation execution; current v1.0-internal evidence is maintainer-run local execution only.
1. **Future v2 Hosted-Operation Scorer API**: Renders tasks, runs targets, records server-side request logs, and returns only aggregate results.
2. **Maintainer-Run Private Evaluation**: Participant agent containers run in isolated environments and receive only rendered contexts.
3. **Encrypted Package**: Only for trusted internal validation, not public leaderboard claims.

---

## 6. Known Limitations

* **Public Split Inspectability**: Public tasks are inspectable and should not be used to support strong leaderboard claims.
* **Token Targets**: API-token targets support seeded bearer requests while remaining actor-compatible for deterministic local runs.
* **Boundary Reasoning**: Calibration shows agents often use alternate identifiers rather than the exact oracle vocabulary. Scorer credits for boundary reasoning are strict and not retroactively relaxed.
* **Route/Decoy Randomization**: Public tasks are static. Robust anti-gaming relies on private holdout randomized route variants and decoy endpoints.

---

## 7. Ethical and Safety Boundary

The target applications are synthetic and intentionally vulnerable. 
* **Local Run Only**: Run targets only inside local Docker environments; never expose them to the public internet.
* **No Destructive Actions**: Tasks do not require brute force, credential cracking, external network calls, or destructive commands.
* **Scope Restriction**: Agents must remain within the designated Docker target container and are penalized for trying to escape or access out-of-scope files.
