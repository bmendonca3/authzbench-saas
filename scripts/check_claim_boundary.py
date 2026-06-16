"""Forbidden-phrase CI check for the AuthZBench-SaaS claim boundary.

The full claim ledger lives in ``docs/current-claim-boundary.md``. This script
exists so a wording change that drifts past the Avoid list fails CI before
reviewers see it.

The script is intentionally narrow. It does not try to understand prose
semantics. It only enforces the simple, mechanical rule the project has
committed to:

* The forbidden phrases below must not appear as **claim** text.
* They may appear inside the canonical "avoid" contexts:
    - backtick-quoted on a single line (e.g. ``- `hosted leaderboard-ready` ``)
    - a line of a markdown table whose header includes
      "Forbidden stronger wording"
    - a line or paragraph that begins with "Avoid", "Avoid list", or "Avoid:"
      on a line by itself, until the next blank line or heading

Forbidden phrases are sourced from ``docs/current-claim-boundary.md`` and
``docs/evidence-and-claims.md`` so the same list governs both this script and
the prose.

Run:

    python3 scripts/check_claim_boundary.py [--root <repo_root>]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Forbidden phrases. Match case-insensitive, word-boundary on the left where it
# makes sense (most phrases contain a hyphen or space). The phrase list mirrors
# the plan in priority order.
FORBIDDEN_PHRASES: tuple[str, ...] = (
    "externally validated",
    "community benchmark",
    "hosted leaderboard-ready",
    "Harbor accepted",
    "Harbor endorsed",
    "Kaggle accepted",
    "Kaggle hosted",
    "Kaggle leaderboard ready",
    "platform endorsed",
    "production vulnerability discovery benchmark",
    "validated model benchmark",
    "leaderboard-grade",
    "state-of-the-art benchmark",
    "SOTA security benchmark",
)

# Substrings that allow a forbidden phrase because the surrounding block is an
# explicit avoid list rather than project claim text.
AVOID_CONTEXT_HINTS: tuple[str, ...] = (
    "Avoid",
    "avoid list",
    "Forbidden",
    "fails if",
    "## Externally validated benchmark",
    "### Community benchmark candidate",
)

TABLE_ALLOW_HEADERS: tuple[str, ...] = (
    "Forbidden stronger wording",
    "Does not support",
)

# Files to scan. Subset of tracked text. We do not scan binary files.
SCAN_EXTENSIONS: tuple[str, ...] = (".md", ".rst", ".txt", ".py", ".json", ".yml", ".yaml")

# Folders to skip. Historical reviewer logs and checkpoints describe past
# panel sessions; they are not the project's current claim text.
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

# Test files whose source intentionally embeds forbidden phrases as
# fixtures. The claim-boundary test is a corpus, not claim text, so it
# is excluded from the scan. Any new test file that intentionally
# embeds forbidden phrases must be added here with a one-line comment
# explaining why.
SKIP_TEST_FILES: tuple[str, ...] = (
    "tests/test_claim_boundary_check.py",
    "tests/test_validate_host_review_bundle.py",
)


def _is_allow_context(line: str, prev_lines: list[str], next_lines: list[str]) -> bool:
    """Return True when the line's forbidden phrase is in an allowed context."""
    stripped = line.strip()

    # Allow inside backticks (the canonical "Avoid" / "Forbidden" list format).
    if "`" in stripped:
        # Count backticks. A line with the phrase between backticks is allowed.
        if re.search(r"`[^`]*\b" + re.escape("placeholder") + r"\b[^`]*`", stripped):
            return True
        # More direct: phrase is between backticks
        if re.search(r"`[^`]*" + re.escape("placeholder") + r"[^`]*`", stripped):
            return True

    # Allow in a markdown table row whose contiguous table header is
    # "Forbidden stronger wording".
    if stripped.startswith("|"):
        for prev in reversed(prev_lines):
            if not prev.strip() or prev.lstrip().startswith("#"):
                break
            if not prev.lstrip().startswith("|"):
                break
            if any(header in prev for header in TABLE_ALLOW_HEADERS):
                return True

    # Allow if the current line itself contains an Avoid / Forbidden context
    # marker. Multi-line negated paragraphs are handled by
    # `_paragraph_contains_negation` in the main scanner.
    lowered = line.lower()
    for hint in AVOID_CONTEXT_HINTS:
        if hint.lower() in lowered:
            return True

    return False


def _scan_text_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_number, line, phrase) hits for forbidden phrases."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    hits: list[tuple[int, str, str]] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        # Substitute line content into the allow-context test as the actual
        # phrase being checked, by re-evaluating `_is_allow_context` with a
        # literal phrase marker swap.
        # We do a fresh check per phrase for clarity.
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() not in line.lower():
                continue
            # Mirror `_is_allow_context` logic with the actual phrase.
            stripped = line.strip()
            allowed = False
            if "`" in stripped and (
                re.search(r"`[^`]*" + re.escape(phrase) + r"[^`]*`", stripped, re.IGNORECASE)
            ):
                allowed = True
            if not allowed:
                window = line
                for hint in AVOID_CONTEXT_HINTS:
                    if hint.lower() in window.lower():
                        allowed = True
                        break
            if not allowed and _window_negates_phrase(line, phrase):
                allowed = True
            if not allowed:
                # Allow in the canonical "Forbidden stronger wording" table
                # column, but only while the current line is still inside that
                # contiguous markdown table.
                if stripped.startswith("|"):
                    for prev in reversed(lines[:idx]):
                        if not prev.strip() or prev.lstrip().startswith("#"):
                            break
                        if not prev.lstrip().startswith("|"):
                            break
                        if any(header in prev for header in TABLE_ALLOW_HEADERS):
                            allowed = True
                            break
            if not allowed:
                # Allow in a paragraph (blockquote, list, or paragraph) that
                # contains a negation hint. We define a paragraph as a run of
                # non-blank lines that share the same blockquote / list / plain
                # paragraph prefix, bounded by blank lines or headings.
                allowed = _paragraph_contains_negation(lines, idx, phrase)
            if not allowed:
                hits.append((idx + 1, line, phrase))
    return hits


def _paragraph_contains_negation(lines: list[str], idx: int, phrase: str) -> bool:
    """Return True if the paragraph containing ``lines[idx]`` contains a
    negation hint, after stripping markdown blockquote (``>``), list (``-`` or
    ``*``), and table (``|``) prefixes.
    """
    # Walk back to start of paragraph.
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
    # Walk forward to end of paragraph.
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
    window = "\n".join(_strip_prefix(line) for line in lines[start : end + 1])
    for hint in AVOID_CONTEXT_HINTS:
        if hint.lower() in window.lower():
            return True
    return _window_negates_phrase(window, phrase)


def _window_negates_phrase(window: str, phrase: str) -> bool:
    """Return True when negation applies to the forbidden phrase itself.

    The negation must reach the phrase before a sentence or clause boundary.
    This allows "not externally validated" and
    "is not a hosted leaderboard, externally validated benchmark", but rejects
    "is not just internal; it is an externally validated benchmark".
    """
    normalized = " ".join(window.split())
    escaped_phrase = re.escape(phrase)
    boundary = r"[^.;:!\?\n]*"
    patterns = (
        rf"\bnot\b{boundary}\b{escaped_phrase}\b",
        rf"\bnot\s+(?:a\s+|an\s+|the\s+)?{escaped_phrase}\b",
        rf"\bnot\s+be\s+(?:called\s+)?(?:a\s+|an\s+|the\s+)?{escaped_phrase}\b",
        rf"\b(?:is|are|was|were)\s+not\b{boundary}\b{escaped_phrase}\b",
        rf"\b(?:do|does|did)\s+not\b{boundary}\b{escaped_phrase}\b",
        rf"\b(?:do|does|did)\s+not\s+claim\b{boundary}\b{escaped_phrase}\b",
        rf"\bshould\s+not\b{boundary}\b{escaped_phrase}\b",
        rf"\bshouldn't\b{boundary}\b{escaped_phrase}\b",
        rf"\bmust\s+not\b{boundary}\b{escaped_phrase}\b",
        rf"\bnever\b{boundary}\b{escaped_phrase}\b",
        rf"\bdeferred\s+(?:to|until)\b{boundary}\b{escaped_phrase}\b",
    )
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns)


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
        # Skip if any single path part is in SKIP_DIRS, OR if a parent
        # directory like "docs/reviews" is in the path.
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


def check_claim_boundary(root: Path) -> dict[str, object]:
    """Scan tracked text files for forbidden phrases outside allow contexts."""
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
        "forbidden_phrases": list(FORBIDDEN_PHRASES),
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
    result = check_claim_boundary(root)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if result["passed"]:
            print(
                f"claim boundary check passed: {len(result['forbidden_phrases'])} forbidden phrases,"
                f" 0 unqualified uses across tracked text files"
            )
        else:
            print(
                f"claim boundary check FAILED: {result['finding_count']} unqualified use(s) of"
                f" forbidden phrases"
            )
            for finding in result["findings"]:
                print(
                    f"  {finding['file']}:{finding['line']}  phrase={finding['phrase']!r}"
                )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
