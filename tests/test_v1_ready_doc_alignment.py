"""Regression test: public docs must not claim v1_ready: true while the fixture says false.

This prevents the class of bug fixed in PR #75 where
docs/harbor-integration-runbook.md said ``v1_ready: true`` while the actual
public-view readiness fixture reported ``v1_ready: false``.

The test scans public documentation files for unqualified ``v1_ready: true``
assertions. Explanatory references that scope the field name (e.g. "the
``v1_ready: true`` field is scoped to...") are allowed.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "artifact" / "expected-output" / "v1-readiness-public-view.json"

# Tracked public doc paths/extensions to scan.
SCAN_GLOBS = (
    "README.md",
    "ROADMAP.md",
    "docs/**/*.md",
    "platform/**/*.md",
    "artifact/README.md",
)

# Excluded paths (review logs, checkpoints, test files, the fixture itself).
EXCLUDE_SUBSTRINGS = (
    "docs/reviews/",
    "docs/checkpoints/",
    "/test_",
    "v1-readiness-public-view.json",
)

# Scoping words that indicate an explanatory reference, not a current-state claim.
SCOPING_WORDS = ("scoped", "field")


def _fixture_v1_ready() -> bool:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return bool(data.get("v1_ready"))


def _is_excluded(path: Path) -> bool:
    posix = path.as_posix()
    return any(ex in posix for ex in EXCLUDE_SUBSTRINGS)


def _scan_docs() -> list[tuple[str, int, str]]:
    """Return (file, line_number, line_text) for unqualified v1_ready: true claims."""
    hits: list[tuple[str, int, str]] = []
    for pattern in SCAN_GLOBS:
        for path in ROOT.glob(pattern):
            if not path.is_file() or _is_excluded(path):
                continue
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "v1_ready: true" not in line and '"v1_ready": true' not in line:
                    continue
                lower = line.lower()
                if any(word in lower for word in SCOPING_WORDS):
                    continue
                hits.append((path.as_posix(), lineno, line.strip()))
    return hits


class V1ReadyDocAlignmentTests(unittest.TestCase):
    def test_fixture_reports_v1_ready_false(self) -> None:
        """Confirm the current fixture state so the scan below is meaningful."""
        self.assertFalse(_fixture_v1_ready(), "Fixture now reports v1_ready: true; update this test.")

    def test_no_unqualified_v1_ready_true_in_public_docs(self) -> None:
        """When the fixture says v1_ready: false, docs must not claim v1_ready: true."""
        if _fixture_v1_ready():
            self.skipTest("Fixture reports v1_ready: true; doc scan not applicable.")
        hits = _scan_docs()
        if hits:
            details = "\n".join(f"  {f}:{n}: {t}" for f, n, t in hits)
            self.fail(f"Unqualified v1_ready: true found in public docs:\n{details}")


if __name__ == "__main__":
    unittest.main()
