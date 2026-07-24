# Score Policy v2: Boundary Normalization

Status: implemented and validated on the preserved 63-task public-run bundles.

## Why the policy changed

An audit of the 14 repeated 63-task public runs found 155 vulnerable-task rows
whose backend exploit replay succeeded under `score-policy-v1`. Only one of
those rows used the oracle's exact hidden `claim` string. In v1, boundary
evaluation ran only after that exact string comparison, even though claim
wording was not a declared weighted score dimension. As a result, 154
replay-proven rows could not receive boundary credit regardless of the
structured boundary they submitted.

The same audit also found that the Kiro and Antigravity adapters could turn a
model command, model-label, or JSON-extraction failure into
`{"findings": []}` with a successful outer exit code. That fallback could
incorrectly pass secure-control tasks.

## `score-policy-v2-boundary-normalization`

Policy v2 makes the following changes:

- Claim text remains required and `claim_exact_match` remains visible, but
  exact oracle wording is diagnostic and does not gate a weighted subscore.
- Boundary credit is binary. Every expected boundary dimension must match;
  partial matches are reported but receive no partial score.
- Exact canonical key/value matches continue to receive credit.
- Structured semantic matches may use normalized case/punctuation, a versioned
  key alias, a task-owned value alias, a small policy-owned value alias, a
  dimension-specific public runtime identifier, or an exact duplicate-free
  expansion of a manifest-declared compound such as `admin_or_auditor`.
- Participant-provided lists are not treated as general alternatives. A
  shotgun list containing several actors, tenants, or values receives no credit.
- Attacker-side and victim-side key aliases are disjoint. An attacker tenant or
  organization identifier cannot satisfy a victim dimension.
- The scorer does not search free-form claim, impact, or evidence prose and
  does not use fuzzy or embedding similarity.
- Required vulnerable-finding fields are enforced: non-empty `claim`,
  non-empty `evidence`, object `boundary`, non-empty `impact`, and list
  `out_of_scope_actions`.
- Participant-controlled request normalization and replay exceptions fail
  closed as stable invalid-submission results. Scorer-owned fixture failures
  are not hidden by this boundary.
- Agent, adapter, timeout, model-label, and output-parse failures cannot be
  scored from a fallback submission.
- `false_positive_rate` counts secure controls with submitted findings, while
  the separate `control_failure_rate` includes any non-passing control row.
  Infrastructure failures therefore cannot masquerade as model over-reporting.

New diagnostics include `claim_exact_match`, `boundary_match_mode`, matched and
missing boundary fields, per-field match bases, `boundary_partial_match`, and
`boundary_field_match_rate`.

## Baseline disposition

The 14 saved 63-task public runs were rescored from their preserved
`submission.json`, `model-output.json`, agent return codes, and task manifests.
Models were not executed again. Every derived summary records:

- source summary, submission-set, score-set, and adapter `model-output.json`
  set hashes;
- distinct source-execution and committed target-benchmark SHAs;
- scorer, runner, and rescore-tool source hashes;
- the target score-policy version;
- a hash of the derived task rows;
- `model_execution_repeated: false`;
- the explicit fail-closed adapter policy.

The registry validator recomputes task aggregates, verifies the task-row hash,
and requires the recorded scorer and rescore-tool hashes to match the current
source. Source-run hashes remain verification handles for the ignored local run
bundles; they are not a signature or independent attestation.

Across the derived summaries, policy v2 reports 153 exploit-proven vulnerable
rows, 58 full boundary passes (1 exact and 57 structured semantic), 133 partial
boundary matches, 42 adapter failures, 12 infrastructure failures, and 46
invalid submissions. Two v1 exploit-proven GLM rows became invalid because the
preserved findings omitted required `out_of_scope_actions`.

Rows with adapter or infrastructure failures are end-to-end model-plus-harness
evidence, not clean model-only capability evidence. Public-split rows are not
private-holdout, hosted-leaderboard, external-review, or platform-acceptance
evidence.

## Comparability

Policy v1 scores remain historical evidence. They must not be directly ranked
against policy v2 scores. Current comparison requires the same task-set
fingerprint, score-policy version, evidence contract, and result derivation.

The offline rescore is suitable for evaluating the preserved submissions under
the corrected scorer. It does not claim that the model was rerun under a new
prompt, adapter, or execution environment.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_scorer*.py'
python3 -m unittest tests/test_runner.py tests/test_rescore_public_run.py
python3 -m unittest tests/test_baseline_registry.py
python3 scripts/validate_baseline_registry.py
```
