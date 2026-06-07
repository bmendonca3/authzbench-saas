# Artifact Install Notes

Prerequisites:

- Python 3.10 or newer
- Git
- Docker and Docker Compose for live HTTP targets or container smoke checks

Install from the repository root:

```bash
python3 -m pip install -e .
```

Public validation without Docker smoke:

```bash
python3 scripts/validate_public.py --include-scripted-baseline
```

Public validation with Docker smoke, when Docker is available:

```bash
python3 scripts/validate_public.py --include-scripted-baseline --include-container-smoke
```

Private holdout validation is maintainer-only and intentionally not part of the
public artifact packet.
