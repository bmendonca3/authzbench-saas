# Host Operations and Leakage Response Runbook

Status: Bounded host/maintainer runbook and custody guide. This runbook outlines operational procedures in the event of suspected or confirmed private holdout task leakage, and defines the rules of holdout data custody.

---

## 1. Privacy and Holdout Custody

AuthZBench-SaaS separates public diagnostic tasks from maintainer-private holdouts. This is a benchmark integrity feature to prevent participant model memorization.

### Host Custody Model
A host or maintainer operating private evaluation should:
1. Freeze an active private pack version.
2. Keep raw private manifests outside public Git.
3. Execute submitter code or submitted bundles in a restricted environment.
4. Let only scorer-controlled code read private oracles.
5. Publish redacted summaries and accepted leaderboard rows only after validation.
6. Rotate packs when leakage, scorer bugs, or task-policy changes require it.

### Public Summary Boundary
Private public summaries may state counts, fingerprints, aggregate metrics, and status labels. They must never reveal per-task private prompts, routes, seeds, or expected outcomes.

### Public vs Non-Public Artifacts
* **Public Artifacts**: Public task manifests (`tasks/`), synthetic target apps (`apps/`), public validation scripts/expected outputs, public-safe aggregate private summaries, private pack counts/fingerprints, sample submissions, and schema examples.
* **Non-Public Artifacts**: Raw private holdout manifests, raw private per-task results, private routes, seeds, object IDs, or oracle details, credentials, tokens, cookies, local private paths, and private panel logs/captures.

---

## 2. Leakage Incident Response Steps

In the event of suspected or confirmed private holdout task leakage:

1. **Halt Submissions**: Immediately disable submission acceptance and scorer queues for the affected active private pack.
2. **Mark Rows Pending Review**: Flag all leaderboard rows evaluated against the affected pack as "pending review".
3. **Retire Active Pack**: Move the active pack role to `retired` in `tasks_private/holdout/rotation-metadata.json`.
4. **Promote Shadow Pack**: Promote the candidate `shadow` pack to `active`. If shadow pack safety is also compromised, prepare a fresh holdout pack.
5. **Regenerate Public-Safe Summaries**: Rebuild the public summaries (`artifact/private-holdout-active-public-summary.json`) using the promoted pack's count-level stats.
6. **Recompute Comparability Keys**: Recompute the comparability keys for active submissions using the new active pack fingerprint.
7. **Publish Incident Note**: Post a public notice detailing the leakage event, retired pack fingerprint, and promoted active pack fingerprint.
8. **Run Host-Presentation Validation**: Run `python3 scripts/validate_host_presentation.py` to ensure all metadata files remain fully compliant and valid.
