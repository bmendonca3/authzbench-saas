"""Tests for ``scripts/check_v1_overclaim.py``.

The CI check enforces a "no positive v1-status over-claim" rule: the
listed phrases are allowed in disclaimer / v2 / backticked / Python
literal contexts, but flagged in plain claim text. The tests below
lock down both the positive case (disclaimers stay) and the negative
case (a real claim is flagged).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_v1_overclaim.py"


def _init_temp_git_repo(cwd: Path) -> None:
    """Initialize a temp git repo and commit everything in it.

    The check script uses `git ls-files` to enumerate scanned files,
    so the fixture files must be committed (not just written) for the
    check to see them.
    """
    subprocess.run(["git", "init", "-q"], cwd=cwd, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=cwd, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=cwd, check=True)
    subprocess.run(["git", "add", "-A"], cwd=cwd, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=cwd, check=True)


def _run_check(cwd: Path) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(cwd), "--json"],
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "result": json.loads(result.stdout) if result.stdout.strip() else {},
    }


class V1OverclaimCheckTests(unittest.TestCase):
    def test_disclaimers_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "docs").mkdir()
            (cwd / "README.md").write_text(
                "# What This Is Not\n\n"
                "- Not an externally reviewed or industry-standard benchmark\n"
                "- Not SaaS-provider validated\n"
                "- Do not describe the project as hosted leaderboard ready\n"
                "  or as having Harbor/Kaggle/platform acceptance\n"
                "\n"
                "## Milestone 7\n"
                "\n"
                "- v2: externally reviewed, scaled, research-grade benchmark\n"
            )
            # Run as if from the temp dir, so the script's `git ls-files`
            # sees an empty tree (which is fine — we use the file directly).
            _init_temp_git_repo(cwd)
            run = _run_check(cwd)
            self.assertEqual(run["returncode"], 0, msg=run["stderr"])
            self.assertTrue(run["result"]["passed"])
            self.assertEqual(run["result"]["finding_count"], 0)

    def test_python_literal_does_not_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "scripts").mkdir()
            (cwd / "scripts" / "detect_overclaims.py").write_text(
                "DISALLOWED = (\n"
                '    "externally reviewed",\n'
                '    "hosted leaderboard ready",\n'
                '    "platform accepted",\n'
                ")\n"
            )
            _init_temp_git_repo(cwd)
            run = _run_check(cwd)
            self.assertEqual(run["returncode"], 0, msg=run["stderr"])
            self.assertTrue(run["result"]["passed"])

    def test_positive_claim_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "docs").mkdir()
            (cwd / "docs" / "README.md").write_text(
                "v1 is externally reviewed and is hosted leaderboard ready.\n"
            )
            _init_temp_git_repo(cwd)
            run = _run_check(cwd)
            self.assertEqual(run["returncode"], 1, msg=run["stderr"])
            self.assertFalse(run["result"]["passed"])
            self.assertGreaterEqual(run["result"]["finding_count"], 1)
            phrases = {f["phrase"] for f in run["result"]["findings"]}
            self.assertIn("externally reviewed", phrases)
            self.assertIn("hosted leaderboard ready", phrases)

    def test_backticked_phrase_does_not_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "docs").mkdir()
            (cwd / "docs" / "README.md").write_text(
                "The phrase `externally reviewed` is in the avoid list.\n"
            )
            _init_temp_git_repo(cwd)
            run = _run_check(cwd)
            self.assertEqual(run["returncode"], 0, msg=run["stderr"])
            self.assertTrue(run["result"]["passed"])

    def test_v2_marker_does_not_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            (cwd / "docs").mkdir()
            (cwd / "docs" / "ROADMAP.md").write_text(
                "## v2 plan\n\n- v2: externally reviewed benchmark\n"
            )
            _init_temp_git_repo(cwd)
            run = _run_check(cwd)
            self.assertEqual(run["returncode"], 0, msg=run["stderr"])
            self.assertTrue(run["result"]["passed"])


if __name__ == "__main__":
    unittest.main()
