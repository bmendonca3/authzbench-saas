# AuthZBench-SaaS Kaggle-Like Rules Template

Status: Draft for host discussion. Not active competition rules.

## 1. Participant Submission Contract
Participants must submit:
- A CSV or JSON manifest (following the `platform/kaggle/sample_submission.csv` format) listing evaluated task IDs and finding paths.
- An evidence/findings bundle containing the exploit proof, targeted HTTP requests/responses, boundary reasoning, and run metadata.
- Submissions must be packaged exactly as specified by the host (e.g., as a ZIP archive, runner image, or staging-environment artifact).

## 2. Eligibility & Participant Responsibilities
- Participants must register with their true identities or approved team names as required by the host.
- Participants must ensure that any automated agents or scripts they develop are run under their direct supervision and comply with target usage policies.
- Sharing of private holdout tasks, exploit details, or scoring oracles between teams is strictly prohibited.

## 3. Scope of Allowed Targets
- Execution is strictly restricted to the synthetic SaaS target applications provided in the active benchmark pack.
- Attempting to exploit, scan, or probe the host infrastructure, scoring system, public leaderboard backend, or any other system outside the specified target ports is a violation of rules and will result in immediate disqualification.

## 4. Network Restrictions
- During evaluation, participant agents must run in a network-isolated environment with no outbound internet connectivity, unless a specific, authenticated gateway is provided by the host.
- Any attempt to bypass network isolation, communicate with external command-and-control servers, or exfiltrate task details via DNS tunneling or other channels is prohibited.

## 5. Secret Handling and Redaction
- Target applications may contain synthetic flags or secrets intended to verify access-control bypasses.
- Agents must expose only the minimum necessary proof (e.g. request logs, resource IDs) as defined in the evidence contract, and must not exfiltrate, publish, or store target secrets outside the authorized evidence directory.
- Participant scripts must redact any local paths, API keys, or user credentials before submitting evidence.

## 6. Disallowed Memorization & Hardcoding
- Submissions must discover vulnerabilities programmatically. Hardcoding specific resource IDs, URLs, or oracle flags to bypass authentication without executing the discovery logic is prohibited.
- Submissions must not hardcode negative findings for secure-control tasks. Scorer checks will verify target request correlation.

## 7. Evidence Retention & Auditing
- The host retains submitted evidence bundles for validation, audit, and appeal resolution.
- Evidence bundles are kept in secure, host-controlled storage and are accessible only to authorized maintainers and reviewers.
- Redacted or metadata-only summaries of submissions may be published for transparency, but raw evidence will not be publicly disclosed without participant consent.

## 8. Private Holdout Confidentiality
- Raw private holdout manifests, target data, and scoring keys are kept in strict custody by the host.
- Participants must not attempt to extract, leak, or reverse-engineer private holdout tasks.
- If a private holdout task is accidentally leaked, participants must notify the maintainers immediately.

## 9. Rerun Policy
- Reruns of submissions against private holdout tasks are executed only under the following conditions:
  - Proven host infrastructure failure or runner misconfiguration.
  - Verified scorer bug or private-pack definition error.
  - Appeals that successfully identify scoring errors.
- Scheduled or participant-requested reruns are not supported for public diagnostic rows.

## 10. Appeals Policy
- Appeals must be submitted within the timeline specified by the host.
- Appeals are accepted only in the case of:
  - Infrastructure failures during evaluation runs.
  - Scoring script bugs that can be demonstrated with public tasks.
  - Documented errors in the private task solutions.
- Disagreements with the benchmark claim boundaries or task design are not grounds for appeals.

## 11. Score Invalidation
- The host reserves the right to invalidate any submission if:
  - Prohibited behaviors or memorization is detected.
  - The submission contains private paths or credentials.
  - The agent performed out-of-scope actions or violated target integrity.
- Invalidated submissions are marked as non-eligible and removed from the active leaderboard.

## 12. Public/Private Leaderboard Display
- **Public Split Rows**: Diagnostic and testing purposes only. Public split rows are not eligible for host/private comparison rows.
- **Private Split Rows**: Host-controlled or maintainer-operated private runs can become `private-candidate` or `private-eligible` rows under a future host pilot after evidence, replay, false-positive, and custody gates pass. This repository does not currently claim hosted leaderboard operation.

## 13. License and Disclosure Terms
- Benchmark code and public tasks are licensed under the repository Apache 2.0 license.
- Participant submissions and evidence remain the property of the participant, but the host is granted a non-exclusive license to run, score, and audit the submission for leaderboard operation.

## 14. Incident Response Contact Path
- Security vulnerabilities, leaks, or platform operational issues must be reported immediately to the maintainers via the contact path specified on the host's competition page or in `.github/SECURITY.md`.
