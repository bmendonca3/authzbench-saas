# IEEE S&P Paper Scaffold

This folder is a working paper scaffold for the released `v0.0` research
artifact. It is intentionally claim-disciplined: the paper should describe
AuthZBench-SaaS as a released benchmark artifact and methodology foundation, not
as a hosted leaderboard or v1/community benchmark.

## Source Documents

- `docs/authzbench-saas-v0.0-technical-report.md`
- `docs/authzbench-saas-v0.0-evidence-map.md`
- `docs/status.md`
- `docs/benchmark-card.md`
- `docs/evidence-and-claims.md`
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

## Build

When the local LaTeX toolchain is available:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error paper/ieee-sp/main.tex
```

The intended class is:

```tex
\documentclass[conference,compsoc]{IEEEtran}
```
