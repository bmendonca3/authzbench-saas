# Boundary-Reasoning Calibration Study

Status: completed public-safe calibration for the historical 49-task v1-prep
public split.

This study audits the historical repeated live HTTP Kiro
`claude-sonnet-4.6` tool-agent runs where exploit replay succeeded but boundary
reasoning did not receive credit. It uses public task manifests and ignored
local public-run bundles only. It does not use private holdout manifests, raw
private captures, private routes, private seeds, reviewer logs, or local
absolute paths.

## Evidence Inputs

| Evidence | Value |
| --- | --- |
| Public split | Historical 49-task v1-prep public split |
| Task count | 49 public tasks |
| Vulnerable task count | 20 |
| Baseline family | `kiro-live-tool-agent-sonnet-current-public-49` |
| Harness | Live HTTP tool-agent |
| Model label | `claude-sonnet-4.6` |
| Run 1 | `20260607T071431380750Z-fc6636f1` |
| Run 2 | `20260607T072056877797Z-2be17ca0` |
| Benchmark commit | `3d4293cd24305ad410ddad8cb68654bf10adc9ff` |
| Public summaries | `baselines/kiro-live-tool-agent-sonnet-current-public-49-run1-summary.json`, `baselines/kiro-live-tool-agent-sonnet-current-public-49-run2-summary.json` |

Both runs report:

- 49/49 model-plan artifacts
- 49/49 per-task tool-probe artifacts
- 49/49 target-request correlation
- zero planner failures
- zero planner parse errors
- zero invalid submissions
- zero secure-control false reports
- 15/20 exploit-proven vulnerable tasks
- 0/20 boundary-reasoning passes
- 0/20 full vulnerable-task passes

## Question

For vulnerable tasks with `exploit_proof: 1`,
`boundary_reasoning: 0`, and `invalid_submission: false`, did the failure look
like:

- true boundary misunderstanding;
- missing required boundary fields;
- reasonable synonym or representation mismatch;
- insufficient task/output instruction; or
- scorer strictness that should be changed for v1?

## Method

The audit used a full census, not a sample, because each run had only 15
exploit-proven vulnerable tasks. For each qualifying task in both runs, the
submitted `finding.boundary` object was compared to the public task's
`expected_boundary` object. At the time, `score-policy-v1` required the
submitted boundary to contain the expected keys and exact public-safe values as
a subset.

The classification below uses the primary cause visible from the submitted
boundary object:

- `schema-key mismatch`: the agent named the right concept but used a key the
  scorer does not accept, such as `actor` instead of `attacker_actor`;
- `identifier representation mismatch`: the agent used generated tenant,
  organization, workspace, file, ticket, or export identifiers where the public
  oracle expects stable public labels such as `alpha`, `beta`, `atlas`, or
  `audit_export`;
- `semantic omission`: the agent's boundary omitted a required concept such as
  required role, required scope, required link state, or victim tenant;
- `expectation/prose boundary`: the boundary object described expected versus
  actual behavior rather than the actor/resource/scope boundary.

## Findings

The repeated runs failed boundary reasoning for the same 15 exploit-proven
vulnerable task IDs. The pattern is stable across runs: agents usually proved
the vulnerable backend behavior, but the boundary object was not in the
oracle-compatible vocabulary.

| Task family | Exploit-proven task IDs | Primary failure pattern |
| --- | --- | --- |
| API tokens | `tok_cross_tenant_secret_read`, `tok_export_scope_bypass` | Scope and actor concepts were present in prose or alternate keys, but required keys such as `attacker_actor`, `victim_tenant`, and `required_scope` were missing. |
| Audit settings | `aud_bfla_member_disables_sso`, `aud_bfla_member_downloads_audit_export`, `aud_bola_nimbus_reads_quasar_audit_log` | Role, resource, and organization boundaries were reported with runtime IDs or alternate keys; required stable labels such as `victim_org`, `resource`, and `required_boundary` were missing. |
| Billing | `bill_bfla_member_enables_export_entitlement`, `bill_bfla_member_plan_change`, `bill_bfla_member_reads_plan_settings` | Admin-only role boundaries were often identified, but `actor` or `actual_actor` did not match `attacker_actor`; one entitlement run used expectation/prose fields instead of boundary keys. |
| File sharing | `fs_bola_northstar_reads_apex_file`, `fs_stale_expired_share_link_access` | Cross-workspace and expired-link concepts were found, but stable victim workspace or required link-state keys were missing. |
| Project management | `pm_bola_owner_reads_beta_task`, `pm_bola_read_alpha_from_beta`, `pm_bola_read_beta_from_alpha` | Cross-tenant reads were proven, but boundaries used runtime tenant IDs or prose fields instead of stable `attacker_actor` and `victim_tenant` labels. |
| Support | `sup_bfla_viewer_closes_ticket`, `sup_bola_acme_reads_orbit_ticket` | Role and cross-org concepts were present, but required keys such as `attacker_actor`, `required_role`, and `victim_org` were missing. |

## Observation Counts

The table counts non-exclusive observations across the 30 audited task-run
cases. These are not mutually exclusive categories: one submission can use an
alternate actor key, include runtime identifiers, and omit an expected stable
label at the same time.

| Observation | Count | Interpretation |
| --- | ---: | --- |
| At least one expected boundary key missing | 30 | Every exploit-proven boundary failure missed at least one key required by the public `expected_boundary` object. |
| Alternate actor, role, or scope key used | 23 | The agent often used keys such as `actor`, `actual_actor`, `actor_role`, `actual_role`, `role`, `missing_scope`, `allowed_roles`, or `scope_held` instead of the oracle key. |
| Runtime identifier used where stable labels are expected | 27 | Many submissions used generated tenant, organization, workspace, file, ticket, export, or resource IDs where the public oracle expects labels such as `alpha`, `beta`, `atlas`, or `audit_export`. |
| Required role or scope represented under an alternate key | 12 | Role/scope concepts were sometimes present but not under `required_role` or `required_scope`. |
| Expected/actual prose fields used as boundary | 7 | Some boundary objects described expected versus actual behavior rather than the actor/resource/scope boundary. |

The repeated runs therefore show a vocabulary and representation gap more than
a simple absence of exploit evidence. They also show why retroactive scorer
normalization would need a new score-policy version: the failures are partly
schema aliases, partly stable-label mismatches, and partly incomplete boundary
objects.

## Interpretation

The audited policy-v1 evidence does not support a simple claim that the tool-agent failed
to understand every authorization boundary. It supports a narrower and more
useful claim:

> The live tool-agent could often produce replayable exploit evidence, but it
> did not reliably translate that evidence into the benchmark's required
> boundary vocabulary.

That was still a real benchmark failure under the then-current policy-v1
contract. The scorer asked for a machine-checkable actor, role, tenant, object,
or scope boundary; a free-form proof with alternate keys was not enough for a
full vulnerable-task pass.

## Decision

Keep the historical v0/v1-prep policy-v1 scores unchanged for existing
comparisons. Do not retroactively award boundary credit to those runs. The zero
boundary-reasoning result is accurate under `score-policy-v1` and should remain
reported as such.

For a future v1 scoring or instruction revision, add a bounded follow-up:

1. Clarify the expected boundary vocabulary in the agent-facing output
   contract.
2. Add examples showing that stable public labels, not runtime IDs, should be
   used when the oracle expects stable labels.
3. Consider an explicit v1 scorer-normalization proposal for safe aliases such
   as `actor` to `attacker_actor`, but only behind a new score-policy version.
4. Rerun affected baselines after any prompt, schema, or scorer change.

## Paper Implication

The paper should frame the current result as a boundary-vocabulary and
structured-reasoning gap, not just as a generic inability to find vulnerable
routes. The strongest supported phrasing is:

> Current public tool-agent runs often replay the vulnerable backend behavior,
> but full vulnerable passes remain blocked because the submitted boundary
> object does not preserve the oracle-compatible actor, role, tenant, object, or
> scope labels.

That phrasing preserves the result's evidence value while avoiding an overclaim
about model cognition.

## Verification Commands

The public summaries and local public-run bundles were inspected with:

```bash
jq '.boundary_reasoning_pass_rate, .exploit_proven_success_rate, .invalid_submission_rate' \
  baselines/kiro-live-tool-agent-sonnet-current-public-49-run1-summary.json
jq '.boundary_reasoning_pass_rate, .exploit_proven_success_rate, .invalid_submission_rate' \
  baselines/kiro-live-tool-agent-sonnet-current-public-49-run2-summary.json
python3 -m unittest discover -s tests
python3 scripts/validate_baseline_registry.py
```

The ignored local run bundles were used only to inspect public per-task
`submission.json` and `score.json` files. They must remain untracked.

## 2026-07-10 Follow-up: policy-v2 disposition

The decision above remains the historical disposition for policy-v1 scores; it
was not rewritten retroactively. A broader audit of all fourteen saved 63-task
public runs subsequently found an additional scorer coupling: boundary
evaluation ran only when `finding.claim` exactly equaled the oracle's hidden
claim string. Of 155 v1 exploit-proven vulnerable rows, only one had that exact
claim. Claim wording was not a declared weighted score dimension, so this gate
prevented the original study from distinguishing structured boundary quality
from oracle-phrase reproduction.

The corrected scorer is versioned as
`score-policy-v2-boundary-normalization`. It evaluates the boundary independently
from claim wording, accepts only bounded structural key/value and
dimension-specific ID normalization, requires every expected dimension for
binary credit, and reports partial matches without scoring them. Policy-v1
scores remain historical and are not directly comparable to v2.

The preserved full-split submissions were rescored offline; models were not
executed again. The current derivation, fail-closed adapter disposition, and
aggregate evidence are documented in
[`score-policy-v2-boundary-normalization.md`](score-policy-v2-boundary-normalization.md).
