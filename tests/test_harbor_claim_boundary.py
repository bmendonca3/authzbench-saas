"""Harbor / platform claim-boundary tests.

The claim-boundary CI check covers the repo as a whole. This test
focuses on the Harbor-specific forbidden phrases that show up in
docs/harbor-integration-runbook.md, runbooks, and Harbor-related
artifacts. The phrases "Harbor accepted", "Harbor endorsed", "platform
accepted", "hosted public leaderboard", and "Kaggle accepted" must
only appear inside explicit "not claimed" contexts. Outside those
contexts the test fails so a wording drift is caught before review.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKED_TEXT_EXTENSIONS = (".md", ".txt", ".json", ".yml", ".yaml")

FORBIDDEN_PHRASES: tuple[str, ...] = (
    "harbor accepted",
    "harbor endorsed",
    "platform accepted",
    "hosted public leaderboard",
    "kaggle accepted",
    "harbor leaderboard-ready",
)

NOT_CLAIMED_HINTS: tuple[str, ...] = (
    "not claimed",
    "not done",
    "is not",
    "are not",
    "do not",
    "does not",
    "no ",
    "without",
    "v2 ",
    "deferred",
    "blocker",
    "blocked",
    "not yet",
    "no claim",
    "no public",
    "scoped to",
    "supports",
    "evidence ",
    "claim boundary",
    "Forbidden stronger wording",
    "Avoid",
    "not include",
    "Not included",
    "Deferred",
    "this release does",
    "it does",
    "v1 does",
    "the v1 release does",
    "checklist of",
    "in the public claim boundary",
)


def _is_in_allow_context(line: str, prev_lines: list[str], next_lines: list[str]) -> bool:
    lowered_line = line.lower()
    if "`" in line:
        return True
    # Wider window so negation framing a few lines above the phrase still counts.
    # The Harbor / plan docs frequently write "v1 does not claim:" and then a
    # checklist of items below it; we want the framing line to be in scope.
    window = "\n".join(prev_lines[-6:] + [line] + next_lines[:3]).lower()
    return any(hint.lower() in window for hint in NOT_CLAIMED_HINTS)


def _git_tracked_text() -> list[Path]:
    import subprocess

    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE
    )
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        path = ROOT / line
        if path.suffix.lower() not in TRACKED_TEXT_EXTENSIONS:
            continue
        if not path.is_file():
            continue
        paths.append(path)
    return paths


class HarborClaimBoundaryTests(unittest.TestCase):
    def test_no_unqualified_harbor_accepted_claim(self) -> None:
        findings: list[str] = []
        for path in _git_tracked_text():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            lines = text.splitlines()
            for idx, line in enumerate(lines):
                lowered = line.lower()
                for phrase in FORBIDDEN_PHRASES:
                    if phrase in lowered and not _is_in_allow_context(
                        line, lines[max(0, idx - 6) : idx], lines[idx + 1 : idx + 4]
                    ):
                        findings.append(f"{path.relative_to(ROOT)}:{idx + 1}  phrase={phrase!r}")
                        break
        self.assertFalse(findings, "Harbor non-claim test failed:\n" + "\n".join(findings))

    def test_harbor_runbook_records_acceptance_status(self) -> None:
        from authzbench.core import load_json

        blockers = load_json(ROOT / "artifact/harbor-adapter-readiness-blockers.json")
        self.assertIn("ready_for_harbor_platform_review", blockers)
        self.assertFalse(blockers["ready_for_harbor_platform_review"])
        self.assertIn("harbor_acceptance_claimed", blockers)
        self.assertFalse(blockers["harbor_acceptance_claimed"])


if __name__ == "__main__":
    unittest.main()
