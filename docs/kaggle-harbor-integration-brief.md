> [!NOTE]
> **Consolidation Notice**: This file is slated for consolidation. Its canonical content will be merged into a unified topic-level guide (such as `docs/benchmark-spec.md` or `docs/scoring-and-submissions.md`) in subsequent consolidation phases.

# Kaggle / Harbor Integration Brief

Status: host-review reference document. This brief summarizes how
AuthZBench-SaaS integrates with Harbor for sandboxed evaluation, what has been
verified locally, and what remains pending from the host/platform side. It does
not claim Harbor acceptance, Kaggle acceptance, hosted leaderboard operation,
or external validation.

## What Is Harbor?

Harbor is a framework for evaluating AI agents in sandboxed environments.
It manages task distribution, agent execution, and verifier-based scoring
within isolated containers.

Public references:

- https://github.com/harbor-framework/harbor
- https://www.harborframework.com/docs/datasets
- https://www.harborframework.com/docs/run-jobs/run-evals

## How AuthZBench-SaaS Uses Harbor

AuthZBench-SaaS can be packaged as a Harbor-compatible dataset. Each
AuthZBench-SaaS task maps to a Harbor task directory containing:

| Harbor artifact       | AuthZBench-SaaS source                                     |
| --------------------- | ---------------------------------------------------------- |
| `instruction.md`      | Task manifest description and scope                        |
| `task.toml`           | Task metadata, difficulty, control type                    |
| `environment/`        | Dockerfile launching the synthetic SaaS target app         |
| `solution/solve.sh`   | Oracle solution script (vulnerable: exit-64 placeholder; secure-control: empty-findings submission) |
| `tests/test.sh`       | Verifier script invoking the AuthZBench-SaaS scorer bridge |
| `verifier/`           | Scorer bridge configuration and task manifest              |

The generated dataset includes a `run_authzbench_saas.yaml` Harbor run config
and a `dataset.toml` root manifest.

## What Has Been Verified Locally

| Milestone                       | Status      | Evidence                                                              |
| ------------------------------- | ----------- | --------------------------------------------------------------------- |
| Harbor dataset skeleton builder | Complete    | `scripts/build_harbor_dataset_skeleton.py`                            |
| Harbor dataset skeleton validator | Complete  | `scripts/validate_harbor_dataset_skeleton.py`                         |
| Local Harbor execution smoke    | Complete    | `artifact/harbor-adapter-smoke.json`                                  |
| Local Harbor parity experiment  | Complete    | `artifact/harbor-parity-experiment.json`                              |
| Per-task reward parity (6/6)    | **Verified** | `parity_verified: true`, `per_task_match_rate: 1.0`, zero disagreements |
| Harbor adapter metadata         | Complete    | `artifact/harbor-adapter-metadata.json`                               |
| Adapter readiness blockers      | Tracked     | `artifact/harbor-adapter-readiness-blockers.json`                     |

### Parity Summary

Using the `secure-control-empty-findings` oracle solution mode on all 6 public
tasks (3 vulnerable + 3 secure-control), Harbor reward scores matched native
AuthZBench-SaaS scores exactly:

- Harbor reward mean: **0.5**
- Native scorer mean: **0.5**
- Per-task disagreements: **0**
- Per-task match rate: **1.0**

Full methodology is documented in
[`docs/harbor-integration-runbook.md`](harbor-integration-runbook.md).

## What Requires Host/Platform Decisions

These items cannot be completed without Kaggle/Harbor platform decisions:

| Item                                  | Why external                                                            |
| ------------------------------------- | ----------------------------------------------------------------------- |
| Kaggle Docker execution spec          | Kaggle must confirm container shape, metadata paths, scoring interface  |
| Kaggle acceptance / hosted benchmark  | Only Kaggle can accept, host, or endorse                               |
| Harbor platform publishing            | Harbor review/publishing/endorsement is external                       |
| SaaS-provider / product-security validation | Requires actual SaaS-security reviewers                          |
| Independent external review           | AppSec, evals, and agent/tooling reviewers must sign off               |
| Third-party participant submissions   | Requires platform operation                                            |
| Hosted private holdout execution      | Requires host-controlled or maintained private runner                   |

## Recommended Next Steps for Kaggle

1. **Review the host-review package**: Start with
   [`docs/host/host-review-package.md`](host/host-review-package.md) for the full
   methodology and artifact inventory.
2. **Run public validation locally**: Execute
   `python3 scripts/validate_public.py --include-scripted-baseline` to
   reproduce the public validation gate.
3. **Decide on hosting model**: Model A (dataset/review package) and Model B
   (maintainer-operated private evaluation pilot) are recommended. See
   [`docs/host/hosting-model.md`](host/hosting-model.md).
4. **Confirm Docker spec**: Provide the expected container shape, artifact
   paths, and scoring interface for Kaggle-hosted execution.
5. **Schedule external reviews**: Independent AppSec, evals, and agent/tooling
   reviews are ready to start. See
   [`docs/reviews/external-review-packet.md`](reviews/external-review-packet.md).

## Explicit Non-Claims

This brief does not claim:

- Harbor platform acceptance or endorsement
- Kaggle acceptance or host-operated scoring/leaderboard service
- External validation completion
- SaaS-provider validation
- Third-party submissions
- `v1` readiness in the external sense
