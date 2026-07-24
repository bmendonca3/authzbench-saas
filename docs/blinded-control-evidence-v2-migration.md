# Blinded Control Evidence V2 Migration

Status: draft contract foundation; not active and not promotable

The repository now carries a machine-readable draft for the next evidence
protocol at `schemas/blinded-control-evidence-v2.schema.json`. It does not
activate v2, change compliant score-policy-v2 results, edit task manifests,
rewrite the benchmark fingerprint, or modify baseline records. The adjacent
registry validator now reads the real runner field, `protocol_version`, while
retaining bounded support for the older `version` alias; conflicting fields or
unverified real blinded-run rows fail closed as originally intended.

The schema separates two participant outputs:

- one vulnerable finding with a concise sequence of host-replayable requests;
- no findings plus exactly one participant-selected control request and its
  predicted HTTP status.

Responses, exploratory notes, and full transcripts are not participant proof
items. The host owns replay responses and writes them to scorer transcripts.
This keeps the submitted proof chain concise and prevents participant-authored
responses from being mistaken for observed backend evidence.

## Current migration audit

Run the report-only audit from the repository root:

```bash
python3 scripts/audit_evidence_contracts.py
```

The current 63-task public set contains 27 vulnerable tasks. Eight have a
valid explicit `evidence_requirements` chain that structurally validates and
replays through its declared response constraints to the final task oracle,
leaving 19 to migrate. Report-only mode exits successfully when the canonical
task set is valid but incomplete. The future activation gate is intentionally
strict and repository-anchored:

```bash
python3 scripts/audit_evidence_contracts.py --require-complete
```

Strict mode exits 1 until all 27 vulnerable tasks are covered. It does not
accept custom globs, so a one-task or zero-vulnerable subset cannot create a
false green activation result. Invalid JSON (including non-finite numbers or
invalid UTF-8), duplicate keys, invalid task manifests, symlinked inputs,
unsatisfiable evidence chains, count mismatches, or an altered schema bundle
exit 2.

The audit reports and pins a canonical JSON SHA-256 for the schema bundle; this
is a contract identity, not a signature or independent attestation. The local
checker verifies that exact identity and its required structure, but does not
claim general Draft 2020-12 meta-schema validation without a JSON Schema
engine. It also reports the audited task-set digest and the replay source-set
digest covering the audit, scorer, manifest validator, core replay code, and
fixture apps, so coverage drift is attributable.

## Required activation gates

The draft must not become `blinded-control-evidence-v2` or enter current
promotion until all of these are complete:

1. Add reviewed evidence chains for all 27 vulnerable tasks and accept the new
   task-set fingerprint.
2. Introduce a new score-policy identifier before moving host-unobserved safety
   out of the weighted score. Historical score-policy-v1/v2 rows keep their
   original meaning.
3. Bind protocol/source-set identity, participant schema, evidence contract,
   score policy, schema digest, task fingerprint, isolation profile, and canary
   suite into the comparability key. The draft run-summary identity fragment
   reserves all of these fields now.
4. Replace working-directory-only isolation with an OS-enforced boundary for
   untrusted filesystem-capable agents and verify a malicious escape fixture.
5. Add positive and negative canaries that detect leaked outcome/task identity,
   omitted control verification, and evidence-shape bypasses.
6. Add the complete v2 manifest to the promotion allowlist, bind its full
   identity, and reclassify legacy/offline-rescore evaluator rows as historical.
   The current gate already rejects unsupported protocol names, conflicting
   aliases, and runner-emitted rows with no protocol identity.
7. Run deterministic local gates, then repeated blinded model baselines. Kiro
   or another adapter is needed only after the protocol is locally converged.

Until then, the schema status remains `draft-non-promotable` and its evidence
contract version remains `evidence-requirements-v2-draft`.
