"""Positive-claim CI check for the AuthZBench-SaaS v1 boundary.

This script complements ``scripts/check_claim_boundary.py``. The claim
boundary checker enforces a hard *avoid* list of forbidden wording; this
script enforces a softer *positive-claim* rule:

* The phrases in ``POSITIVE_V1_OVERCLAIM_PHRASES`` are not forbidden.
  They appear legitimately in disclaimers, v2 roadmaps, and "do not
  describe the project as…" warnings.
* But if a tracked line *asserts* that v1 is one of those things in a
  positive / status-claim voice, that is an over-claim and must fail CI
  before reviewers see it.

A line is treated as a *positive claim* when:

* it contains one of the phrases, AND
* it does not contain a negation / disclaimer hint, AND
* it is not inside a backticked or table-cell quote, AND
* it is not inside a "v2:" / "v1.1:" / "v2.x" milestone marker.

The negation / disclaimer hint list is the same one used by
``scripts/check_claim_boundary.py`` so the two scripts share a single
vocabulary for "this is a non-claim sentence".

Run:

    python3 scripts/check_v1_overclaim.py [--root <repo_root>]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Phrases that, if used in a positive v1-status voice, would be an
# over-claim. Match case-insensitive, word-boundary where it makes sense.
# Order matches the Round 1 over-claim grep so CI output is stable.
POSITIVE_V1_OVERCLAIM_PHRASES: tuple[str, ...] = (
    "externally reviewed",
    "hosted leaderboard ready",
    "platform accepted",
    "SaaS-provider validated",
    "third-party endorsed",
    "v1 external readiness",
)

# Substrings that, when found on the same line or paragraph, signal the
# phrase is being used in a non-claim / disclaimer / v2 voice. This is
# the same vocabulary as scripts/check_claim_boundary.py so both scripts
# treat "Not…", "Do not…", "Avoid…", "deferred to v2" as non-claim
# contexts.
NEGATION_HINTS: tuple[str, ...] = (
    "Avoid",
    "avoid list",
    "Forbidden",
    "not a",
    "not an",
    "is not",
    "are not",
    "was not",
    "were not",
    "do not",
    "does not",
    "did not",
    "should not",
    "shouldn't",
    "never",
    "not be",
    "not be called",
    "not claim",
    "not ",
    "does not claim",
    "do not claim",
    "did not claim",
    "must not",
    "remain optional",
    "deferred to",
    "deferred until",
    "external gates",
    "## Externally validated benchmark",
    "### Community benchmark candidate",
)

# Markers that pull a phrase into a non-current milestone (v1.1, v2,
# v2.x) where "externally reviewed" or "hosted leaderboard ready" is
# describing future scope, not v1 status. A line that starts with or
# contains "v2:" / "v1.1:" / "v2.x" / "v2 " before the phrase is
# treated as non-claim.
MILESTONE_MARKERS: tuple[str, ...] = (
    "v2:",
    "v2.",
    "v2 ",
    "v1.1:",
    "v1.1.",
    "v1.1 ",
)

# Files to scan. Subset of tracked text. We do not scan binary files.
SCAN_EXTENSIONS: tuple[str, ...] = (".md", ".rst", ".txt", ".py", ".json", ".yml", ".yaml")

# Folders to skip. Historical reviewer logs and checkpoints describe
# past panel sessions; they are not the project's current claim text.
SKIP_DIRS: tuple[str, ...] = (
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "panel-logs",
    ".handoff",
    ".kiro",
    "docs/checkpoints",
    "docs/reviews",
)

# Test files whose source intentionally embeds phrases as fixtures. The
# check is a corpus, not claim text, so it is excluded from the scan.
# Any new test file that intentionally embeds positive-claim phrases
# must be added here with a one-line comment explaining why.
SKIP_TEST_FILES: tuple[str, ...] = (
    "tests/test_claim_boundary_check.py",
    "tests/test_v1_overclaim_check.py",
)


def _is_positive_claim_context(line: str) -> bool:
    """Return True when the line is asserting v1 status in a positive voice.

    A line is *not* a positive claim (and is therefore allowed) when:

    * it contains a negation / disclaimer hint, OR
    * it carries a v1.1 / v2 milestone marker, OR
    * the phrase is inside a backticked or table-cell quote.
    """
    lowered = line.lower()

    # 1. Backticked quote or table-cell: the phrase is named, not claimed.
    if "`" in line and re.search(
        r"`[^`]*" + r"[a-z _.-]+" + r"[^`]*`", line, re.IGNORECASE
    ):
        # Cheap filter: any line that has matched backticks around text is
        # a quote, not a claim. The actual phrase match happens upstream.
        if re.search(r"`[^`]+`", line):
            return False

    # 2. Markdown table row: the phrase is in a cell, not a claim.
    stripped = line.lstrip()
    if stripped.startswith("|"):
        return False

    # 3. Milestone marker: a "v2:" or "v1.1:" line is forward-looking.
    for marker in MILESTONE_MARKERS:
        if marker in line:
            return False

    # 4. Negation / disclaimer hint: the line is disavowing, not claiming.
    for hint in NEGATION_HINTS:
        if hint.lower() in lowered:
            return False

    return True


def _paragraph_prefix(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith(">"):
        return ">"
    if stripped.startswith("-") or stripped.startswith("*"):
        return "list"
    if stripped.startswith("|"):
        return "table"
    return "para"


def _strip_prefix(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith(">"):
        return stripped[1:].lstrip()
    if stripped.startswith("-") or stripped.startswith("*"):
        return stripped[1:].lstrip()
    if stripped.startswith("|"):
        return stripped.lstrip("|").rstrip("|")
    return stripped


def _python_literal_line_indices(lines: list[str]) -> set[int]:
    """Return line indices that fall inside a multi-line Python literal
    such as ``NAME = (...)`` / ``[...]`` / ``{...}``.

    These lines hold constants the script uses to *detect* claims in
    other files, so the phrases they contain are not claims. A line is
    considered part of a literal when a previous non-blank line opened
    a parenthesis / bracket / brace on a `NAME = ...` assignment and a
    later non-blank line closes it.
    """
    opens = ("(", "[", "{")
    closes = (")", "]", "}")
    indices: set[int] = set()
    in_block = False
    depth = 0
    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        if not in_block:
            # Look for `NAME = (` / `NAME = [` / `NAME = {` opener, with the
            # opener on this line or the previous non-blank line.
            if re.match(r"^[A-Za-z_][A-Za-z0-9_.]*\s*=\s*[({\[]", stripped):
                in_block = True
                depth = sum(line.count(c) for c in opens) - sum(line.count(c) for c in closes)
                if depth > 0:
                    indices.add(idx)
            continue
        # We are inside a block. Count opens/closes.
        depth += sum(line.count(c) for c in opens) - sum(line.count(c) for c in closes)
        indices.add(idx)
        if depth <= 0:
            in_block = False
            depth = 0
    return indices


def _paragraph_has_negation_or_milestone(lines: list[str], idx: int) -> bool:
    """Return True if the paragraph containing lines[idx] carries a
    negation hint or a milestone marker anywhere in its run."""
    start = idx
    while start > 0:
        prev = lines[start - 1]
        if not prev.strip():
            break
        if prev.startswith("# "):
            break
        if _paragraph_prefix(prev) != _paragraph_prefix(lines[idx]):
            break
        start -= 1
    end = idx
    while end + 1 < len(lines):
        nxt = lines[end + 1]
        if not nxt.strip():
            break
        if nxt.startswith("# "):
            break
        if _paragraph_prefix(nxt) != _paragraph_prefix(lines[idx]):
            break
        end += 1
    window = "\n".join(_strip_prefix(line) for line in lines[start : end + 1]).lower()
    for hint in NEGATION_HINTS:
        if hint.lower() in window:
            return True
    for marker in MILESTONE_MARKERS:
        if marker in window:
            return True
    return False


def _scan_text_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_number, line, phrase) hits that look like
    positive v1-status over-claims."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    hits: list[tuple[int, str, str]] = []
    lines = text.splitlines()
    literal_lines = _python_literal_line_indices(lines)
    for idx, line in enumerate(lines):
        for phrase in POSITIVE_V1_OVERCLAIM_PHRASES:
            if phrase.lower() not in line.lower():
                continue
            if idx in literal_lines:
                # Inside a Python source-level constant (e.g.
                # `DISALLOWED_OVERCLAIMS = (...)`). Not a claim.
                continue
            if not _is_positive_claim_context(line):
                continue
            if not _paragraph_has_negation_or_milestone(lines, idx):
                hits.append((idx + 1, line, phrase))
    return hits


def _git_tracked_files(root: Path) -> list[Path]:
    """Return the list of tracked files we should scan."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        path = root / line
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        skip_prefixes = ("docs/reviews/",)
        rel_str = str(path.relative_to(root))
        if any(rel_str.startswith(prefix) for prefix in skip_prefixes):
            continue
        if rel_str in SKIP_TEST_FILES:
            continue
        if path.suffix.lower() not in SCAN_EXTENSIONS:
            continue
        if not path.is_file():
            continue
        paths.append(path)
    return paths


def check_v1_overclaim(root: Path) -> dict[str, object]:
    """Scan tracked text files for positive v1-status over-claims."""
    findings: list[dict[str, object]] = []
    for path in _git_tracked_files(root):
        for line_number, line, phrase in _scan_text_file(path):
            findings.append(
                {
                    "file": str(path.relative_to(root)),
                    "line": line_number,
                    "phrase": phrase,
                    "text": line.strip()[:200],
                }
            )
    return {
        "positive_v1_overclaim_phrases": list(POSITIVE_V1_OVERCLAIM_PHRASES),
        "finding_count": len(findings),
        "passed": not findings,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full result as JSON instead of a short summary.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    result = check_v1_overclaim(root)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if result["passed"]:
            print(
                f"v1 over-claim check passed: {len(result['positive_v1_overclaim_phrases'])} phrases,"
                f" 0 positive v1-status over-claims across tracked text files"
            )
        else:
            print(
                f"v1 over-claim check FAILED: {result['finding_count']} positive v1-status over-claim(s)"
            )
            for finding in result["findings"]:
                print(
                    f"  {finding['file']}:{finding['line']}  phrase={finding['phrase']!r}"
                )
                print(f"    > {finding['text']}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
