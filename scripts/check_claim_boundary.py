"""Forbidden-phrase CI check for the AuthZBench-SaaS claim boundary.

The full claim ledger lives in ``docs/current-claim-boundary.md``. This script
exists so a wording change that drifts past the Avoid list fails CI before
reviewers see it.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Expanded forbidden phrases matching the canonical table
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
    "hosted leaderboard",
    "hosted submission operation",
    "public leaderboard operation",
    "community-benchmark",
    "SaaS-validated",
    "real-world validated",
    "AppSec-reviewed",
    "v1 release-ready",
    "v1.0 released",
    "open for third-party submissions",
    "community submission open",
)

# Substrings that allow a forbidden phrase in canonical files
AVOID_CONTEXT_HINTS: tuple[str, ...] = (
    "Avoid",
    "avoid list",
    "Forbidden",
    "fails if",
    "Externally validated benchmark",
    "Community benchmark candidate",
    "Do not claim",
    "Do not describe",
    "Do not",
    "Does not claim",
    "does not describe",
    "not describe",
    "unsupported",
    "Not done",
    "what it is not",
    "what it does not",
    "not yet",
    "neither",
)

TABLE_ALLOW_HEADERS: tuple[str, ...] = (
    "Forbidden stronger wording",
    "Does not support",
    "What It Does Not Prove",
    "What It Does Not Claim",
)

CANONICAL_CLAIM_FILES: tuple[str, ...] = (
    "docs/claims-and-evidence.md",
    "docs/benchmark-spec.md",
    "docs/v1-readiness-checklist.md",
    "docs/reviewer-walkthrough.md",
    "README.md",
    "ROADMAP.md",
    "platform/kaggle/faq.md",
    "platform/kaggle/rules-template.md",
    "docs/v0-release-plan.md",
    "docs/harbor-integration-runbook.md",
    "docs/harbor-parity-per-task-contract.md",
    "docs/launch-report.md",
    "docs/authzbench-saas-v0.0-technical-report.md",
)

SCAN_EXTENSIONS: tuple[str, ...] = (".md", ".rst", ".txt", ".py", ".json", ".yml", ".yaml")

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

SKIP_TEST_FILES: tuple[str, ...] = (
    "tests/test_claim_boundary_check.py",
    "tests/test_validate_host_review_bundle.py",
)


def _window_negates_phrase(window: str, phrase: str) -> bool:
    """Return True when negation applies to the forbidden phrase itself."""
    normalized = " ".join(window.split())
    escaped_phrase = re.escape(phrase) + r"s?"
    boundary = r"[^.;!\?\n]*"
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
        rf"\bwithout\s+claiming\b{boundary}\b{escaped_phrase}\b",
        rf"\bwithout\b{boundary}\b{escaped_phrase}\b",
        rf"\bno\s+claim\b{boundary}\b{escaped_phrase}\b",
        rf"\bno\b{boundary}\b{escaped_phrase}\b",
        rf"\bneither\b{boundary}\b{escaped_phrase}\b",
        rf"\b{escaped_phrase}\b{boundary}\bdeferred\b",
        rf"\b{escaped_phrase}\b{boundary}\bnot\s+(?:done|claimed)\b",
        rf"\b{escaped_phrase}\b{boundary}\bpending\b",
        rf"\b(?:later|future|planned|unsupported|roadmap|v2)\b{boundary}\b{escaped_phrase}\b",
        rf"\b{escaped_phrase}\b{boundary}\b(?:later|future|planned|unsupported|roadmap|v2)\b",
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


def _paragraph_contains_negation(lines: list[str], idx: int, phrase: str, rel_path_str: str) -> bool:
    """Return True if paragraph has negation or (for canonical files) avoid hints."""
    start = idx
    while start > 0:
        prev = lines[start - 1]
        if not prev.strip():
            break
        if prev.startswith("# "):
            break
        prev_pref = _paragraph_prefix(prev)
        idx_pref = _paragraph_prefix(lines[idx])
        if prev_pref != idx_pref:
            if not (prev_pref in ("list", "para") and idx_pref in ("list", "para")):
                break
        start -= 1

    end = idx
    while end + 1 < len(lines):
        nxt = lines[end + 1]
        if not nxt.strip():
            break
        if nxt.startswith("# "):
            break
        nxt_pref = _paragraph_prefix(nxt)
        idx_pref = _paragraph_prefix(lines[idx])
        if nxt_pref != idx_pref:
            if not (nxt_pref in ("list", "para") and idx_pref in ("list", "para")):
                break
        end += 1

    window = "\n".join(_strip_prefix(line) for line in lines[start : end + 1])

    # Allow avoid hints in canonical claim files
    if any(rel_path_str.endswith(f) for f in CANONICAL_CLAIM_FILES):
        for hint in AVOID_CONTEXT_HINTS:
            if hint.lower() in window.lower():
                return True

    return _window_negates_phrase(window, phrase)


def _is_in_allowed_table_column(line: str, header: str, phrase: str) -> bool:
    """Return True if phrase resides inside allowed columns of a markdown table."""
    header_cols = [c.strip() for c in header.split("|")[1:-1]]
    allow_indices = [i for i, h in enumerate(header_cols) if any(allow_h.lower() in h.lower() for allow_h in TABLE_ALLOW_HEADERS)]
    if not allow_indices:
        return False
    line_cols = [c.strip() for c in line.split("|")[1:-1]]
    for idx in allow_indices:
        if idx < len(line_cols) and phrase.lower() in line_cols[idx].lower():
            return True
    return False


def _section_contains_avoid_hint(lines: list[str], idx: int, rel_path_str: str) -> bool:
    """Return True if the current markdown section contains any avoid context hint."""
    if not any(rel_path_str.endswith(f) for f in CANONICAL_CLAIM_FILES):
        return False
    # Find start of section (upwards to nearest line starting with '#')
    start = idx
    while start > 0:
        if lines[start].lstrip().startswith("#"):
            break
        start -= 1
    # Find end of section (downwards to next line starting with '#')
    end = idx
    while end + 1 < len(lines):
        if lines[end + 1].lstrip().startswith("#"):
            break
        end += 1

    # Scan all lines in this range [start, end] for any avoid context hint
    for i in range(start, end + 1):
        for hint in AVOID_CONTEXT_HINTS:
            if hint.lower() in lines[i].lower():
                return True
    return False


def _is_allow_context(line: str, lines: list[str], idx: int, phrase: str, rel_path_str: str) -> bool:
    """Consolidated single allow-context validation helper."""
    stripped = line.strip()

    # 1. Backtick / Quote literal formats on current line
    if "`" in stripped:
        if re.search(r"`[^`]*" + re.escape(phrase) + r"[^`]*`", stripped, re.IGNORECASE):
            return True
    if '"' in stripped:
        if re.search(r'"[^"]*' + re.escape(phrase) + r'[^"]*"', stripped, re.IGNORECASE):
            return True
    if "'" in stripped:
        if re.search(r"'[^']*" + re.escape(phrase) + r"[^']*'", stripped, re.IGNORECASE):
            return True

    # 2. Avoid hints (only in canonical files)
    if any(rel_path_str.endswith(f) for f in CANONICAL_CLAIM_FILES):
        for hint in AVOID_CONTEXT_HINTS:
            if hint.lower() in line.lower():
                return True

    # 3. Direct grammatical negation on the current line
    if _window_negates_phrase(line, phrase):
        return True

    # 4. Markdown table header column check
    if stripped.startswith("|"):
        # Find contiguous table header
        for prev in reversed(lines[:idx]):
            if not prev.strip() or prev.lstrip().startswith("#"):
                break
            if not prev.lstrip().startswith("|"):
                break
            if any(header.lower() in prev.lower() for header in TABLE_ALLOW_HEADERS):
                # Header matches. Verify that the phrase is in that specific column
                if _is_in_allowed_table_column(line, prev, phrase):
                    return True
                break

    # 5. Check paragraph-level negation or avoid list contexts
    if _paragraph_contains_negation(lines, idx, phrase, rel_path_str):
        return True

    # 6. Check section-level scan for avoid/negation hints
    if _section_contains_avoid_hint(lines, idx, rel_path_str):
        return True

    return False


def _scan_text_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line_number, line, phrase) hits for forbidden phrases."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    # Resolve path relative to repository ROOT
    try:
        rel_path_str = str(path.relative_to(ROOT))
    except ValueError:
        rel_path_str = path.name
        path_parts = path.parts
        for f in CANONICAL_CLAIM_FILES:
            f_parts = Path(f).parts
            if len(path_parts) >= len(f_parts) and path_parts[-len(f_parts):] == f_parts:
                rel_path_str = f
                break

    hits: list[tuple[int, str, str]] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() not in line.lower():
                continue
            if not _is_allow_context(line, lines, idx, phrase, rel_path_str):
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
    parser = argparse.ArgumentParser(description="Check claim boundaries.")
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
