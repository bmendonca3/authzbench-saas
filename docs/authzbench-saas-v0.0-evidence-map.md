# AuthZBench-SaaS v0.0 Evidence Map

This file maps paper/report claims to public-safe repository evidence. It is
intended to keep external writing grounded and to prevent accidental
overclaiming.
On the `v1-task-expansion` branch, the live public split has expanded to 49
tasks. This file preserves the frozen v0.0 46-task release evidence map.

## Source Files Inspected

Primary release and scope files:

- [`README.md`](../README.md)
- [`ROADMAP.md`](../ROADMAP.md)
- [`docs/benchmark-card.md`](benchmark-card.md)
- [`docs/launch-report.md`](launch-report.md)
- [`docs/release-evidence.json`](release-evidence.json)
- [`docs/baseline-credibility.md`](baseline-credibility.md)
- [`docs/evidence-and-claims.md`](evidence-and-claims.md)
- [`docs/status.md`](status.md)
- [`docs/release-notes-v0.0.md`](release-notes-v0.0.md)

Methodology and scoring files:

- [`docs/methodology.md`](methodology.md)
- [`docs/score-policy.md`](score-policy.md)
- [`docs/result-schema.md`](result-schema.md)
- [`docs/leaderboard-schema.md`](leaderboard-schema.md)
- [`docs/score-stability-policy.md`](score-stability-policy.md)

Baseline and evidence files:

- [`baselines/baseline-registry.json`](../baselines/baseline-registry.json)
- [`baselines/scripted-baseline-public-46-summary.json`](../baselines/scripted-baseline-public-46-summary.json)
- [`baselines/kiro-qwen3-coder-next-current-public-46-run1-summary.json`](../baselines/kiro-qwen3-coder-next-current-public-46-run1-summary.json)
- [`baselines/kiro-qwen3-coder-next-current-public-46-run2-summary.json`](../baselines/kiro-qwen3-coder-next-current-public-46-run2-summary.json)
- [`baselines/kiro-claude-haiku-4.5-current-public-46-run1-summary.json`](../baselines/kiro-claude-haiku-4.5-current-public-46-run1-summary.json)
- [`baselines/kiro-claude-haiku-4.5-current-public-46-run2-summary.json`](../baselines/kiro-claude-haiku-4.5-current-public-46-run2-summary.json)
- [`baselines/kiro-claude-sonnet-4.6-current-public-46-run1-summary.json`](../baselines/kiro-claude-sonnet-4.6-current-public-46-run1-summary.json)
- [`baselines/kiro-claude-sonnet-4.6-current-public-46-run2-summary.json`](../baselines/kiro-claude-sonnet-4.6-current-public-46-run2-summary.json)
- [`baselines/kiro-glm-5-current-public-46-run1-summary.json`](../baselines/kiro-glm-5-current-public-46-run1-summary.json)
- [`baselines/kiro-glm-5-current-public-46-run2-summary.json`](../baselines/kiro-glm-5-current-public-46-run2-summary.json)
- [`baselines/kiro-live-tool-agent-sonnet-current-public-46-summary.json`](../baselines/kiro-live-tool-agent-sonnet-current-public-46-summary.json)
- [`baselines/kiro-live-tool-agent-sonnet-current-public-46-run2-summary.json`](../baselines/kiro-live-tool-agent-sonnet-current-public-46-run2-summary.json)
- [`leaderboard_sources/haiku-private-holdout-fb9e4c7-run1-redacted-source-summary.json`](../leaderboard_sources/haiku-private-holdout-fb9e4c7-run1-redacted-source-summary.json)
- [`leaderboard_sources/haiku-private-holdout-fb9e4c7-run2-redacted-source-summary.json`](../leaderboard_sources/haiku-private-holdout-fb9e4c7-run2-redacted-source-summary.json)
- [`leaderboard_sources/tool-agent-private-holdout-21e92c7-run1-redacted-source-summary.json`](../leaderboard_sources/tool-agent-private-holdout-21e92c7-run1-redacted-source-summary.json)

## Supported Claims

| Claim | Status | Evidence | Notes |
| --- | --- | --- | --- |
| AuthZBench-SaaS v0.0 is a released benchmark artifact. | Supported | `v0.0` tag and GitHub Release; release notes; release evidence | This does not imply hosted leaderboard readiness. |
| The public split contains 6 synthetic SaaS apps. | Supported | `README.md`, `docs/benchmark-card.md`, task manifests, manifest validator | Apps are local fixtures, not production targets. |
| The v0.0 public split contains 46 tasks. | Supported | `baselines/baseline-registry.json`, `docs/status.md`, manifest validator | Public tasks are inspectable; live v1-prep has expanded to 49. |
| The v0.0 public split contains 19 vulnerable tasks and 27 secure controls. | Supported | `baseline-registry.json`, `docs/benchmark-card.md`, `docs/status.md` | v0.0 secure controls include denial and authorized-allow controls. |
| The control mix is 16 denial controls and 11 authorized-allow controls. | Supported | `baseline-registry.json`, `README.md`, `docs/status.md` | Authorized-allow controls are central to false-positive discipline. |
| The benchmark uses deterministic backend replay. | Supported | `docs/methodology.md`, `docs/score-policy.md`, scorer and transcript docs | Replay is scorer-owned and stronger than prose-only claims. |
| Scoring separates exploit proof, boundary reasoning, false positives, control execution, safety, and live-target coverage. | Supported | `docs/score-policy.md`, `docs/result-schema.md`, baseline summaries | `mean_score` is retained only as a compatibility field. |
| Frozen v0.0 public baselines include five repeated model/agent families. | Supported | `baselines/baseline-registry.json`, `docs/baseline-credibility.md` | Four no-tools model families plus one live HTTP tool-agent family; current v1 reruns are pending. |
| The frozen v0.0 public live HTTP tool-agent has two 46-task runs with full target-request correlation. | Supported | `kiro-live-tool-agent-sonnet-current-public-46*.json`, `docs/baseline-credibility.md` | Public-split evidence only; not current v1 evidence. |
| Public baselines show exploit replay can succeed while boundary reasoning remains weak. | Supported | Frozen v0.0 public baseline summaries | v0.0 model/tool-agent rows have `boundary_reasoning_pass_rate: 0.0`. |
| Protected private-holdout evidence exists without publishing private task bodies. | Supported | Redacted source summaries, `docs/release-evidence.json`, privacy checks | Only aggregate/redacted claims are public-safe. |
| One private no-tools row is release-candidate eligible under the tracked schema. | Supported | `leaderboard_submissions/2026-06-06/haiku-private-holdout-host-isolated.leaderboard.json`, `validate_leaderboard_submission.py` | This is not hosted leaderboard operation or a private model ranking claim. |
| Raw private holdouts, results, captures, and raw panel logs are not tracked. | Supported when `git ls-files` check returns empty | Privacy check command listed below | Must be rechecked before any public-facing release update. |

## Partially Supported Claims

| Claim | Status | Evidence | Limitation |
| --- | --- | --- | --- |
| AuthZBench-SaaS can support leaderboard-style submission validation. | Partially supported | `docs/leaderboard-schema.md`, validation scripts, example rows | No hosted public leaderboard exists yet. |
| Protected private evaluation supports anti-gaming. | Partially supported | Maintainer-only private pack validation and redacted evidence | Rotating holdouts and broader isolation are still v1 work. |
| Tool-agent evidence is workflow-real. | Partially supported | Public live HTTP tool-agent runs with target-request correlation | Private repeated tool-agent leaderboard rows are not complete. |
| Baseline variance can be analyzed. | Partially supported | Repeated current public runs | Statistical analysis is not yet a full research-grade section. |
| The benchmark is ready for a paper/technical report. | Partially supported | v0.0 release evidence and current docs | External review and comparison against other benchmarks remain future work. |

## Unsupported Claims

| Claim | Why unsupported |
| --- | --- |
| AuthZBench-SaaS is a hosted public leaderboard. | The repository has schemas and validators, not a hosted submission service. |
| AuthZBench-SaaS is v1/community-scale. | Task count, rotating holdouts, external review, and third-party operations are not mature enough yet. |
| Public-split scores are private leaderboard rankings. | Public tasks are inspectable and intended for reproducibility/integration. |
| The benchmark proves production vulnerability-discovery ability. | Targets are synthetic local fixtures. |
| The benchmark measures broad cyber capability. | Scope is SaaS authorization proof quality. |
| Current baselines establish definitive model rankings. | Runs are diagnostic, public-split evidence with limited scale and no private leaderboard operation. |
| Boundary-reasoning failures alone prove the models cannot reason about authorization. | The scorer is strict and should be studied; the result is a benchmark signal, not a universal model-capability conclusion. |

## Current Baseline Table

| Baseline | Harness | Tasks | V0 passed | Exploit proof | Boundary reasoning | False positives | Authorized allow | Invalid submissions | Target coverage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Scripted sanity baseline | scripted | 46 | 46 | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 | n/a |
| Qwen run 1 | no-tools model | 46 | 27 | 0.0 | 0.0 | 0.0 | 1.0 | 0.0 | n/a |
| Qwen run 2 | no-tools model | 46 | 27 | 0.0526 | 0.0 | 0.0 | 1.0 | 0.0217 | n/a |
| Claude Haiku run 1 | no-tools model | 46 | 26 | 0.2632 | 0.0 | 0.037 | 1.0 | 0.0 | n/a |
| Claude Haiku run 2 | no-tools model | 46 | 27 | 0.0526 | 0.0 | 0.0 | 1.0 | 0.0 | n/a |
| Claude Sonnet run 1 | no-tools model | 46 | 27 | 0.6316 | 0.0 | 0.0 | 1.0 | 0.0 | n/a |
| Claude Sonnet run 2 | no-tools model | 46 | 26 | 0.4211 | 0.0 | 0.037 | 1.0 | 0.0 | n/a |
| GLM run 1 | no-tools model | 46 | 27 | 0.2105 | 0.0 | 0.0 | 1.0 | 0.0 | n/a |
| GLM run 2 | no-tools model | 46 | 27 | 0.0526 | 0.0 | 0.0 | 1.0 | 0.0 | n/a |
| Claude Sonnet tool-agent run 1 | live HTTP tool-agent | 46 | 27 | 0.7368 | 0.0 | 0.0 | 1.0 | 0.0 | 1.0 |
| Claude Sonnet tool-agent run 2 | live HTTP tool-agent | 46 | 27 | 0.7368 | 0.0 | 0.0 | 1.0 | 0.0 | 1.0 |

## Verification Commands

Use these commands when refreshing paper/report claims:

```bash
python3 scripts/validate_baseline_registry.py
python3 scripts/validate_public.py --include-scripted-baseline
python3 scripts/validate_v0_release.py --allow-incomplete
git ls-files tasks_private/holdout results captures docs/reviews/panel-logs
```

In a maintainer checkout with private holdouts present, strict release checks can
also be run:

```bash
python3 scripts/validate_v0_release.py
python3 scripts/validate_protected_private_evidence.py \
  --summary leaderboard_sources/haiku-private-holdout-fb9e4c7-run1-redacted-source-summary.json \
  --summary leaderboard_sources/haiku-private-holdout-fb9e4c7-run2-redacted-source-summary.json \
  --summary leaderboard_sources/tool-agent-private-holdout-21e92c7-run1-redacted-source-summary.json \
  --min-run-count 2 \
  --require-host-isolation
```

## Writing Rules For External Summaries

Use:

- `released v0.0 benchmark artifact`
- `public split`
- `protected private-holdout evidence`
- `deterministic backend replay`
- `false-positive controls`
- `public-split baseline evidence`
- `not a hosted leaderboard`

Avoid:

- `definitive benchmark`
- `hosted leaderboard-ready`
- `validated model ranking`
- `production vulnerability discovery`
- `broad cyber capability`
- `state of the art`
- `v1/community-scale benchmark`
