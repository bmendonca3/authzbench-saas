# IEEE S&P Paper Scaffold

This folder is a working paper scaffold for the current v1-prep research
artifact. It is intentionally claim-disciplined: the paper should describe
AuthZBench-SaaS as a released v0.0 benchmark artifact plus active v1-prep
methodology foundation, not as a hosted leaderboard or v1/community benchmark.

## Source Documents

- `docs/authzbench-saas-v0.0-technical-report.md`
- `docs/authzbench-saas-v1-prep-technical-report.md`
- `docs/authzbench-saas-v0.0-evidence-map.md`
- `docs/status.md`
- `docs/benchmark-spec.md`
- `docs/claims-and-evidence.md`
- `baselines/baseline-registry.json`
- `docs/task-quality-matrix.json`

## Tables

Shared tables are generated from repository artifacts:

```bash
python3 scripts/generate_paper_tables.py
```

After generation, tracked table files should be stable:

```bash
git diff --exit-code -- paper/shared
```

Treat both commands as a reproducibility check before paper commits. A clean
diff means the shared LaTeX tables still match the tracked benchmark artifacts.

## Figures

Public-safe chart sources live under:

```text
docs/assets/benchmark-charts/
```

Likely paper figures:

- `model-pass-rate`
- `exploit-proven-success`
- `false-positive-rate`
- `boundary-reasoning`
- `task-mix`
- `evidence-readiness`

The current scaffold documents these charts but does not require conversion to
compile the draft. If figures are added to `main.tex`, convert SVG sources to
PDF under `paper/ieee-sp/figures/` first and keep the conversion command in this
README.

Figure inclusion is deferred for the current scaffold. The SVG chart sources are
public-safe and useful for draft planning, but the paper needs a deliberate
conversion choice before committing figure PDFs:

- task mix: source `docs/assets/benchmark-charts/task-mix.svg`
- exploit proof vs boundary reasoning: sources
  `docs/assets/benchmark-charts/exploit-proven-success.svg` and
  `docs/assets/benchmark-charts/boundary-reasoning.svg`
- false-positive rate: source
  `docs/assets/benchmark-charts/false-positive-rate.svg`
- evidence readiness: source
  `docs/assets/benchmark-charts/evidence-readiness.svg`

Before enabling figures in `main.tex`, verify that the converted files are
readable in a two-column IEEE layout and that they do not imply hosted
leaderboard operation or private-holdout rankings.

## Build

When the local LaTeX toolchain is available:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error paper/ieee-sp/main.tex
```

The intended class is:

```tex
\documentclass[conference,compsoc]{IEEEtran}
```
