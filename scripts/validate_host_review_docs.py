#!/usr/bin/env python3
"""Validator for required host-review documentation files."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "docs/host/README.md",
    "docs/host/host-review-package.md",
    "docs/host/host-status-and-reproducibility.md",
    "docs/host/hosting-model.md",
    "docs/host/host-operations-runbook.md",
    "docs/host/host-review-walkthrough.md",
    "platform/kaggle/rules-template.md",
    "platform/kaggle/competition-page-draft.md",
    "platform/kaggle/faq.md",
]

REQUIRED_TERMS = {
    "docs/host/host-review-package.md": [
        "platform acceptance",
        "hosted leaderboard operation",
        "external validation",
        "third-party submissions",
    ],
    "docs/host/host-status-and-reproducibility.md": [
        "Actions Workflow Run ID",
        "Latest Verified Commit",
        "Conclusion",
        "python3 scripts/validate_host_presentation.py",
    ],
    "docs/host/hosting-model.md": [
        "Model A",
        "Model B",
        "Model C",
        "CSV",
        "replay-based scoring",
    ],
}


def validate_host_docs(root: Path) -> dict:
    errors = []
    for rel_path in REQUIRED_DOCS:
        doc_path = root / rel_path
        if not doc_path.is_file():
            errors.append(f"Missing required host document: {rel_path}")
            continue

        try:
            content = doc_path.read_text(encoding="utf-8")
            if not content.strip():
                errors.append(f"Document is empty: {rel_path}")
                continue

            # Check for obvious unfinished draft markers
            if "TODO:" in content or "FIXME" in content:
                errors.append(f"Document contains TODO or FIXME markers: {rel_path}")

            # Check for required terms
            if rel_path in REQUIRED_TERMS:
                for term in REQUIRED_TERMS[rel_path]:
                    if term not in content:
                        errors.append(f"Document {rel_path} is missing required term: '{term}'")

        except Exception as e:
            errors.append(f"Failed to read {rel_path}: {e}")

    return {"passed": len(errors) == 0, "errors": errors}


def main():
    result = validate_host_docs(ROOT)
    if not result["passed"]:
        print("Host review documentation validation FAILED:", file=sys.stderr)
        for err in result["errors"]:
            print(f"- {err}", file=sys.stderr)
        sys.exit(1)
    print("Host review documentation validation PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
