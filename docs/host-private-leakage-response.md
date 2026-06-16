# Host Private Holdout Leakage Response Runbook

Status: Bounded host/maintainer runbook.

This runbook outlines operational procedures in the event of suspected or confirmed private holdout task leakage.

## Incident Response Steps

1. **Halt Submissions**: Immediately disable submission acceptance and scorer queues for the affected active private pack.
2. **Mark Rows Pending Review**: Flag all leaderboard rows evaluated against the affected pack as "pending review".
3. **Retire Active Pack**: Move the active pack role to `retired` in `tasks_private/holdout/rotation-metadata.json`.
4. **Promote Shadow Pack**: Promoted the candidate `shadow` pack to `active`. If shadow pack safety is also compromised, prepare a fresh holdout pack.
5. **Regenerate Public-Safe Summaries**: Rebuild the public summaries (`artifact/private-holdout-active-public-summary.json`) using the promoted pack's count-level stats.
6. **Recompute Comparability Keys**: Recompute the comparability keys for active submissions using the new active pack fingerprint.
7. **Publish Incident Note**: Post a public notice detailing the leakage event, retired pack fingerprint, and promoted active pack fingerprint.
8. **Run Host-Presentation Validation**: Run `python3 scripts/validate_host_presentation.py` to ensure all metadata files remain fully compliant and valid.
