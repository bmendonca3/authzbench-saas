# Execute Now: T005A Behavior Truth Only

Do not ask a question. Make these exact mechanical edits now, run the two
checks, inspect the three-file diff, and report. Do not delegate.

Repository: `<canonical-checkout>`

Edit only:

- `artifact/scored-cohort-contract.v1.json`
- `scripts/validate_scored_cohort_contract.py`
- `tests/test_scored_cohort_contract.py`

Do not edit any other path. Preserve all Phase 0 files and the completion
packet.

## Contract Repair

For every public cluster, remove the redundant `behaviors` field and retain one
canonical `behavior_counts` object. Set it to these exact manifest-derived
values:

```text
api-token-authorized-operations:
  authorized_allow=2
api-token-cross-tenant-secret-access:
  authorized_allow=1, denial=1, vulnerable=2
api-token-scope-enforcement:
  denial=2, vulnerable=2
audit-authorized-operations:
  authorized_allow=3
audit-bfla-privilege-escalation:
  denial=1, vulnerable=2
audit-cross-org-log-access:
  denial=1, vulnerable=2
billing-authorized-operations:
  authorized_allow=3
billing-cross-org-access:
  denial=2
billing-member-privilege-escalation:
  denial=3, vulnerable=6
file-sharing-authorized-operations:
  authorized_allow=2
file-sharing-cross-workspace-access:
  denial=1, vulnerable=2
file-sharing-share-link-access:
  denial=2, vulnerable=2
project-mgmt-authorized-operations:
  authorized_allow=2
project-mgmt-cross-tenant-access:
  denial=3, vulnerable=4
support-authorized-operations:
  authorized_allow=2
support-bfla-ticket-escalation:
  denial=3, vulnerable=4
support-cross-org-ticket-access:
  denial=2, vulnerable=1
```

The aggregate must be exactly 63 tasks: 27 vulnerable, 21 denial, and 15
authorized-allow.

## Validator Repair

Load each public manifest and derive:

```text
vulnerable       if expected_vulnerable is true
denial           if expected_vulnerable is false and control_type == "denial"
authorized_allow if expected_vulnerable is false and control_type == "authorized_allow"
```

For each cluster, require the declared:

- `task_count`;
- sorted unique `apps`;
- `app_count`; and
- `behavior_counts`

to equal values derived from its task IDs. Reject unknown/malformed behavior.
Require aggregate totals 63 / 27 / 21 / 15. Include those behavior totals in
the validator result and compact CLI output.

Remove `behaviors` from the required cluster fields.

## Tests

Update the real-contract test to assert exact 63 / 27 / 21 / 15 totals. Add
separate fail-closed mutations for:

- a wrong cluster `apps` value; and
- a wrong cluster `behavior_counts` value.

Keep all existing mutation tests.

Run only:

```text
python3 scripts/validate_scored_cohort_contract.py
python3 -m pytest -q tests/test_scored_cohort_contract.py
git diff --check
```

Return the exact totals, test count, and confirmation that only these three
T005 files changed during this job.
