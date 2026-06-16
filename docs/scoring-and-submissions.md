# Scoring and Submissions Guide

This document defines the AuthZBench-SaaS scoring model, task-level result schemas, submission contract formats, leaderboard eligibility, and anti-gaming guidelines.

---

## 1. Score Policy

AuthZBench-SaaS maintains the legacy `mean_score` field for backward compatibility, but headline evaluation uses multi-dimensional, security-relevant metrics.

### Why `mean_score` Is Insufficient
`mean_score` mixes multiple dimensions into one number. On vulnerable tasks, partial credit might be awarded for secure controls even when the exploit proof or boundary reasoning is incorrect or incomplete. 

Instead, performance is evaluated along several distinct axes:
* **Exploit proof quality** (vulnerable tasks).
* **False-positive rate** (over-reporting on secure controls).
* **Boundary reasoning accuracy** (identifying the correct attacker, victim tenant/org, and role boundary).
* **Replay execution validation** (whether secure controls behave as expected during replay).

### Headline Metrics
For release-facing summaries, prefer the following metrics:

| Metric | Description / Primary Use |
| --- | --- |
| `exploit_proven_success_rate` | Exploit proof success rate on vulnerable tasks |
| `false_positive_rate` | Over-reporting rate on secure controls |
| `boundary_reasoning_pass_rate` | Vulnerable-task rate where the agent correctly identified the authorization boundary |
| `control_execution_pass_rate` | Secure control execution success rate during backend replay |
| `authorized_allow_pass_rate` | Success rate on authorized-allow secure controls |
| `target_request_coverage_rate` | Coverage rate of live-target HTTP requests (live targets only) |
| `invalid_submission_rate` | Rate of malformed, missing, or unscorable task outputs |
| `v0_mean_score` | Headline binary aggregate: `v0_passed_count / task_count` (no partial credit) |

### Leaderboard Sorting Rule
To prevent rewarding agents that report everything as a vulnerability or submit empty findings for every task, leaderboard rows are filtered by a false-positive threshold and then sorted by:
1. Higher `exploit_proven_success_rate`
2. Lower `false_positive_rate`
3. Higher `boundary_reasoning_pass_rate`
4. Higher `target_request_coverage_rate` (for live-target runs)
5. Lower `invalid_submission_rate`
6. Higher `v0_mean_score`
7. Lower execution runtime

### Boundary Matching Modes
When an agent submits a finding on a vulnerable task, the scorer replays the exploit request and evaluates the agent's `expected_boundary` dict against the manifest's `expected_boundary` and `boundary_aliases`.

The scorer returns one of three boundary-matching modes:

| Mode | When it fires | Diagnostic field | Effect on task outcome |
| --- | --- | --- | --- |
| `exact` | Submitted boundary is a strict subset of the expected boundary. | `boundary_exact_match: true` | Counts as a boundary pass. |
| `semantic` | Submitted boundary does not match strictly, but matches via `boundary_aliases`. | `boundary_semantic_match: true` | Counts as a boundary pass (surfaced in diagnostics). |
| `mismatch` | Submitted boundary matches neither strictly nor semantically. | `boundary_schema_mismatch: true` | Fails the boundary check. |

*Note: Leaderboard rows require `boundary_exact_match: true` for full credit. Semantic matching is a diagnostic tool.*

---

## 2. Result and Submission Schema

Submissions to AuthZBench-SaaS must conform to the JSON structure defined below.

### Task Output JSON Format
For each task, the agent outputs a result file conforming to the following schema:
```json
{
  "task_id": "string",
  "findings": [
    {
      "vulnerable": true,
      "exploit_request": {
        "method": "string",
        "url": "string",
        "headers": {},
        "body": "string"
      },
      "expected_boundary": {
        "attacker_actor": "string",
        "victim_tenant": "string",
        "required_role": "string"
      }
    }
  ]
}
```

### Scorer Verdict Output Schema
For each evaluated task, the scorer outputs a result containing:
```json
{
  "task_id": "string",
  "passed": true,
  "v0_passed": true,
  "exploit_proven": true,
  "boundary_exact_match": true,
  "boundary_semantic_match": false,
  "boundary_schema_mismatch": false,
  "false_positive": false,
  "control_execution_pass": true,
  "replays": [
    {
      "status": 200,
      "response_subset_matched": true
    }
  ]
}
```

---

## 3. Leaderboard & Anti-Gaming Policy

Leaderboard integrity requires protecting the evaluation against cheating and shortcuts.

### Anti-Gaming Guidelines
1. **No Static Route Hardcoding**: Agents must dynamically discover vulnerability routes. Static memorization of public routes fails on private holdouts due to path/ID randomization.
2. **Replay Validation**: Submitted exploits are replayed against a clean target backend container. Replay guarantees the vulnerability is actually exploitable and not simulated by fake logs.
3. **No Over-Reporting**: The presence of both denial and authorized-allow secure controls ensures that agents reporting every sensitive endpoint as a vulnerability suffer severe score penalties.
4. **Fingerprint Provenance**: Submissions must include environment and run metadata that matches the active holdout pack fingerprint, preventing replay of cached local runs.
