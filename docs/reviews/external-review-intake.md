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
  Follow-up artifact:
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
- Keep reviewer identity private unless publication permission is explicit.
- Replace every unresolved marker before copying evidence into
  `docs/reviews/external-review-summary.json`.
- For `accepted` or `unresolved` findings, add a tracked follow-up artifact or
  cite an existing commit SHA before running readiness validation.
- If the reviewer reports no findings, record one explicit no-finding decision
  with `decision: rejected` only when there is a concrete reason no code or doc
  change is needed.
- Run structured validation (e.g., using parser helpers in `validate_v1_readiness.py`) after
  updating the summary to ensure format compliance for future v2 milestones.

## Public-Safety Rules

- Do not include private holdout manifests, task identifiers, private routes,
  private seeds, raw private outputs, captures, credentials, or local absolute
  paths.
- Do not paste reviewer logs or private correspondence into the public repo.
- Summarize findings in public-safe language and link only to tracked public
  artifacts or existing commit SHAs.
