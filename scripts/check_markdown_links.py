#!/usr/bin/env python3
"""Local relative link checker for markdown files in the repository."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
KAGGL_DIR = ROOT / "platform/kaggle"
README_PATH = ROOT / "README.md"


def check_markdown_links(files: list[Path], root: Path = ROOT) -> dict:
    errors = []
    link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    root = root.resolve()

    for file_path in files:
        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            for line_idx, line in enumerate(content.splitlines(), start=1):
                for match in link_pattern.finditer(line):
                    link = match.group(1).strip()
                    # Skip external links and anchors
                    if (
                        link.startswith("http://")
                        or link.startswith("https://")
                        or link.startswith("mailto:")
                        or link.startswith("#")
                    ):
                        continue

                    # Strip anchor part if present
                    path_part = link.split("#")[0]
                    if not path_part:
                        continue

                    # Resolve relative path
                    target_path = (file_path.parent / path_part).resolve()
                    rel_file = file_path.relative_to(root) if root in file_path.parents else file_path
                    try:
                        target_path.relative_to(root)
                    except ValueError:
                        errors.append(
                            f"{rel_file}:L{line_idx}: Link target '{link}' escapes repository root"
                        )
                        continue

                    rel_target = target_path.relative_to(root)
                    if not target_path.exists():
                        errors.append(
                            f"{rel_file}:L{line_idx}: Broken link '{link}' "
                            f"(resolved to non-existent: {rel_target})"
                        )
        except Exception as e:
            errors.append(f"Failed to read {file_path}: {e}")

    return {"passed": len(errors) == 0, "errors": errors}


def main():
    # Gather all markdown files
    all_files = list(DOCS_DIR.glob("**/*.md")) + list(KAGGL_DIR.glob("**/*.md")) + [README_PATH]
    files = []
    for f in all_files:
        rel = str(f.relative_to(ROOT))
        if rel.startswith("docs/reviews/") or rel.startswith("docs/checkpoints/"):
            continue
        files.append(f)

    result = check_markdown_links(files)
    if not result["passed"]:
        print("Markdown link check FAILED:", file=sys.stderr)
        for err in result["errors"]:
            print(f"- {err}", file=sys.stderr)
        sys.exit(1)
    print("Markdown link check PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
