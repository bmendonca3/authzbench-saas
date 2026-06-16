> [!NOTE]
> **Consolidation Notice**: This file is slated for consolidation. Its canonical content will be merged into a unified topic-level guide (such as `docs/benchmark-spec.md` or `docs/scoring-and-submissions.md`) in subsequent consolidation phases.

# Task Quality Rubric

Use this rubric when adding public tasks, reviewing private holdouts, or asking
an external reviewer to evaluate AuthZBench-SaaS task quality. It is meant to
raise benchmark quality without exposing private holdout details.

For a generated public-task audit view, see
[`task-quality-matrix.md`](task-quality-matrix.md). The matrix summarizes
coverage and evidence-readiness signals; this rubric remains the qualitative
review standard.

The public validation gate also enforces the machine-readable acceptance
contract in
[`../artifact/task-quality-gate-contract.json`](../artifact/task-quality-gate-contract.json)
through `scripts/validate_task_quality_gate.py`.

## Review Scores

Score each category from 0 to 2:

| Score | Meaning |
| ---: | --- |
| 0 | missing, weak, ambiguous, or unsafe |
| 1 | acceptable for alpha/public rehearsal |
| 2 | strong enough for release-candidate or holdout use |

## Categories

| Category | What To Check |
| --- | --- |
| SaaS realism | The task resembles a plausible SaaS authorization boundary: tenant, org, workspace, role, token, object, invite, export, billing, sharing, or settings access. |
| Boundary clarity | The expected attacker, victim tenant/org/workspace, required role/scope, and protected object are unambiguous. |
| Replay proof | A finding can be verified through deterministic backend replay, not just prose. Multi-step workflows use explicit `evidence_requirements` with request shape and response checks when setup or sequence matters. |
| Control quality | The task includes denial or authorized-allow controls that would catch over-reporting, under-reporting, or route guessing. |
| False-positive trap | Secure controls are tempting enough that an agent must reason, not simply return `findings: []` or report every sensitive route. |
| Anti-gaming resistance | Seeded IDs, route aliases, decoys, and private-holdout variants reduce value from hardcoded public-task answers. |
| Safety boundary | The task does not require external targets, credential attacks, brute force, destructive behavior, or non-local systems. |
| Documentation clarity | Rendered context gives enough information for a real agent to act while keeping scorer oracles and private holdout details hidden. |

## Release-Candidate Bar

A task family should not be treated as release-candidate quality unless:

- vulnerable tasks have replayable proof and correct boundary checks
- secure controls include both denial and authorized-allow coverage where
  applicable
- every oracle, control, and evidence requirement has an integer `status` check
  or a non-empty `body_contains` check; empty body-only checks are not
  acceptable replay proof
- every task declares non-empty `allowed_hosts` containing only local benchmark
  fixture app names
- the task avoids real customer data, real SaaS branding, and secrets
- public tasks do not copy private holdout routes, seeds, IDs, or oracle bodies
- manifest validation and relevant scorer tests pass
- at least one reviewer has checked the task family against this rubric

## External Review Packet

For external review, provide only public-safe material:

- this rubric
- the public task manifests being reviewed
- rendered public task contexts
- scorer/result schema docs
- aggregate public baseline summaries
- known limitations from `docs/benchmark-card.md`

Do not provide private holdout manifests, hidden seeds, private routes, oracle
bodies, raw private run bundles, or private target logs.
