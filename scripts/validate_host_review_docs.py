#!/usr/bin/env python3
"""Validator for required host-review documentation files."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "docs/host-review-package.md",
    "docs/host-facing-one-page-summary.md",
    "docs/kaggle-hosting-model.md",
    "docs/evaluation-for-hosts.md",
    "docs/solution-file-contract.md",
    "docs/privacy-and-holdout-custody.md",
    "docs/host-reproducibility-matrix.md",
    "docs/host-baseline-summary.md",
    "docs/host-architecture.md",
    "docs/host-packet-versioning.md",
    "docs/host-private-leakage-response.md",
    "docs/host-review-walkthrough-transcript.md",
    "platform/kaggle/rules-template.md",
    "platform/kaggle/competition-page-draft.md",
    "platform/kaggle/faq.md",
]


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
            # We allow "TBD by host" or similar in templates, but check for generic TODOs
            if "TODO:" in content or "FIXME" in content:
                errors.append(f"Document contains TODO or FIXME markers: {rel_path}")

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
