> [!NOTE]
> **Consolidation Notice**: This file is slated for consolidation. Its canonical content will be merged into a unified topic-level guide (such as `docs/benchmark-spec.md` or `docs/scoring-and-submissions.md`) in subsequent consolidation phases.

# Methodology

AuthZBench-SaaS measures a specific capability: whether an AI agent can prove a
SaaS authorization boundary failure with backend evidence and avoid reporting
secure controls.

## Benchmark Thesis

Most broad security-agent benchmarks measure exploit success against CVEs, CTFs,
or vulnerable applications. AuthZBench-SaaS focuses on the bug class that often
requires multi-actor reasoning:

- Which actor is making the request?
- Which tenant, organization, or project owns the object?
- Which role should be required?
- What should the denial/control request return?
- Is the behavior reportable, or is it authorized product behavior?

## Contamination Resistance

Each task uses a seed. Target apps derive tenant IDs, object IDs, and actor tokens
from that seed. Public tasks can therefore render concrete values per run while
keeping manifests readable and reducing hardcoded-solution value.

Planned hardening for the real v0:

- private holdout tasks
- randomized route aliases
- multiple seeds per task
- scorer-side hidden oracle details
- versioned public releases

## Task Types

| Type | Description | Expected output |
| --- | --- | --- |
| BOLA | Cross-tenant object read/write succeeds | One finding with replayable proof |
| BFLA | Non-admin reaches admin function | One finding with replayable proof |
| Secure control: denial | Backend correctly denies unsafe access | `findings: []` |
| Secure control: authorized-allow | Backend correctly allows authorized behavior | `findings: []` |

## Oracles

Every task has a machine-verifiable oracle. For vulnerable tasks, submitted
evidence must replay against the seeded backend and return the expected status
and response subset. When a vulnerable task depends on workflow sequence, it can
declare `evidence_requirements`; each required replay step must match both the
expected request shape and response expectation before the task receives
exploit-proof credit. Vulnerable tasks also declare an
`expected_boundary` so the scorer can check whether the agent named the correct
attacker, victim tenant or organization, and required role. For secure controls,
the submission must contain no findings and the control request must return the
expected status and response subset.

Secure-control manifests include `control_type` so result summaries can separate
denial controls from authorized-allow controls. This matters because an agent
that reports every sensitive endpoint as a bug should fail authorized-allow
controls even when it avoids denial-control false positives.

## Safety Boundary

The benchmark is intentionally vulnerable, but agents should still be scored down
for out-of-scope actions. Public tasks should not require destructive behavior,
credential attacks, external network calls, brute force, or attacks against hosts
outside the local Docker network.
