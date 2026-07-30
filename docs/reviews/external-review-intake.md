# External Review Intake

Status: public-safe intake form for independent reviewers. This file helps a
reviewer return evidence in the same shape that
`docs/reviews/external-review-summary.json` and
its validator require. It is not review evidence by
itself.

## Reviewer Response Form

Use role and scope, not private identity, unless the reviewer grants permission.

```text
Lane:
Reviewer role and scope:
Review date:
Reviewed commit SHA:
No-redistribution terms accepted: yes | no
Conflict-of-interest declaration:
Reviewer identity publication permission: yes | no

Artifacts reviewed:
- 

Questions reviewed:
- 

Disposition:
findings | no_findings

Findings or no-finding record:
- Finding:
  Decision: accepted | rejected | unresolved
  Summary:
  Claim-boundary impact:
  Follow-up artifact or remediation commit:
```

## Lane-Specific Minimums

Application security review should cover task realism, BOLA/BFLA quality,
role/scope/sharing boundaries, unsafe-public-detail risk, and false-positive
controls.

Benchmark/evals methodology review should cover split design, score semantics,
variance framing, stale/current evidence separation, release claim boundary, and
leaderboard eligibility language.

AI-agent/tooling review should cover harness assumptions, tool access,
target-request correlation, model/agent comparability, benchmark fingerprint,
run provenance, and run-bundle evidence.

## Maintainer Intake Checklist

- Confirm the response maps to exactly one required lane.
- Confirm the reviewer accepted the no-redistribution terms and supplied a
  conflict-of-interest declaration before any controlled private review.
- Keep reviewer identity private unless publication permission is explicit.
- Bind the review to one real, frozen Git commit before review begins.
- An unresolved decision keeps the lane pending; it cannot be copied into a
  completed summary.
- An accepted finding needs a descendant remediation commit that changes the
  cited tracked path. A pre-existing file is not remediation evidence.
- A rejected finding needs a concrete public-safe rationale.
- If the reviewer reports no findings, record one explicit no-finding decision
  and an accepting overall disposition; do not encode “no findings” as a
  rejected finding.
- Run `python3 scripts/validate_v2_external_validation.py` for the public-safe
  pending structure. Run it again with `--require-complete` only after all
  reviewers have returned real records and remediation is complete.

## Template-To-Summary Transformation

`external-review-response.template.json` is deliberately not the public summary
schema. To prepare the canonical summary:

1. Start from the template and replace every placeholder with review facts.
2. Set the top-level `schema_version` to `external-review-summary-v1`.
3. Remove `template_only` and retain the concrete public claim boundary.
4. Keep each canonical `registry_lane_id`, reviewed commit SHA, review date,
   overall disposition, artifacts, questions, decisions, and claim-boundary
   impact.
5. Keep the corresponding registry lane and summary lane coherent.
6. Validate the JSON and Markdown summary together with the combined command
   above. The summary is canonical public evidence; the template is never
   evidence.

## Public-Safety Rules

- Do not include private holdout manifests, task identifiers, private routes,
  private seeds, raw private outputs, captures, credentials, or local absolute
  paths.
- Do not paste reviewer logs or private correspondence into the public repo.
- Summarize findings in public-safe language and link only to tracked public
  artifacts or remediation commits.
- Controlled per-task private responses use
  `schemas/private-appsec-review.schema.json` and stay under the ignored
  reviewer-environment `private-review-responses/` path. Only a record matching
  `schemas/private-review-aggregate.schema.json` may be considered for a
  tracked aggregate projection.
