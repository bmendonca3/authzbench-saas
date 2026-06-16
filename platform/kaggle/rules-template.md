# AuthZBench-SaaS Kaggle-Like Rules Template

Status: Draft for host discussion. Not active competition rules.

## Participant Submission
Participants submit:
- A CSV/manifest file (following `platform/kaggle/sample_submission.csv` format) listing task IDs and finding paths.
- An evidence/findings bundle containing the exploit proof, targeted HTTP requests, boundary reasoning, and run metadata.

## Allowed Automation
- Agents may interact only with the provided target applications.
- Agents may not attempt to access private holdout manifests, solution files, raw private results, credentials, or maintainer-only paths.
- Agents may not exfiltrate target secrets beyond the benchmark evidence contract.

## Prohibited Behavior
- **Private Task Leakage**: Storing or attempting to leak private holdout manifests or solutions.
- **Route/Oracle Hardcoding**: Hardcoding specific URLs or oracles to bypass authentication rather than discovering them.
- **Over-Reporting**: Submitting exploit findings on secure controls to inflate scores.
- **Malformed Submissions**: Evading false-positive checks by submitting invalid/corrupt JSON.
- **Unauthorized Actions**: Attempting to access host filesystems or network hosts outside approved target app services.

## Public Split
The public split is diagnostic only. Runs against the public split are not eligible for private/final leaderboard rows.

## Private Split
Evaluation runs against the private split are host-controlled or maintainer-operated. Raw private manifests and solution files are excluded from public artifacts.

## Appeals
Appeals are accepted only in the case of runner infrastructure failure, runner misconfiguration, scorer bug, private-pack error, or metadata mismatch.

## Publication
Only redacted leaderboard rows, aggregate statistics, pack fingerprints, and public-safe summaries are published to the public leaderboard.
