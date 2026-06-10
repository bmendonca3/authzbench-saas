from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Block coding-agent co-author branding from entering repository history.
DISALLOWED_COAUTHOR_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^Co-authored-by:\s*Cursor\s*<cursoragent@cursor\.com>\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"cursoragent@cursor\.com", re.IGNORECASE),
)


def find_disallowed_trailer_hits(message: str) -> list[str]:
    hits: list[str] = []
    for pattern in DISALLOWED_COAUTHOR_PATTERNS:
        if pattern.search(message):
            hits.append(pattern.pattern)
    return hits


def scan_git_history(cwd: Path) -> None:
    if not (cwd / ".git").exists():
        return
    result = subprocess.run(
        ["git", "log", "--format=%H%x1e%B%x1e", "HEAD"],
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    blocks = [block for block in result.stdout.split("\x1e") if block.strip()]
    for block in blocks:
        sha, _, body = block.partition("\x1e")
        if not sha:
            continue
        hits = find_disallowed_trailer_hits(body)
        if hits:
            raise SystemExit(
                "disallowed commit message trailer found in history:\n"
                f"  commit {sha.strip()}\n"
                "Remove Co-authored-by: Cursor <cursoragent@cursor.com> and similar agent branding."
            )


def check_message_file(path: Path) -> None:
    message = path.read_text(encoding="utf-8")
    if find_disallowed_trailer_hits(message):
        raise SystemExit(
            "commit message rejected: Co-authored-by: Cursor <cursoragent@cursor.com> is not allowed in this repository."
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reject disallowed coding-agent co-author trailers.")
    parser.add_argument(
        "commit_message_file",
        nargs="?",
        help="Path to the commit message file (for commit-msg hooks).",
    )
    parser.add_argument(
        "--scan-history",
        action="store_true",
        help="Scan current branch history for disallowed trailers.",
    )
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]

    if args.commit_message_file:
        check_message_file(Path(args.commit_message_file))
    if args.scan_history or not args.commit_message_file:
        scan_git_history(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
