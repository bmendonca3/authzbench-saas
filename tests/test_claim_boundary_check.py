"""Tests for ``scripts/check_claim_boundary.py``.

The CI check enforces a small, intentional forbidden-phrase list against the
current claim boundary. The tests below lock down both the positive case
(phrases allowed in avoid-list contexts) and the negative case (phrases
flagged in plain claim text).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_claim_boundary.py"


def _run_check(cwd: Path) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(cwd), "--json"],
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode not in (0, 1):
        raise AssertionError(f"unexpected exit {result.returncode}: {result.stderr}")
    return json.loads(result.stdout)


class ClaimBoundaryCheckTests(unittest.TestCase):
    def test_current_repo_passes(self) -> None:
        result = _run_check(ROOT)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["finding_count"], 0)

    def test_forbidden_phrase_in_claim_text_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "readme.md").write_text(
                "This benchmark is a hosted leaderboard-ready, externally validated community benchmark.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/readme.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root,
                check=True,
                text=True,
            )
            result = _run_check(root)
        self.assertFalse(result["passed"], result)
        phrases = sorted(finding["phrase"] for finding in result["findings"])
        self.assertIn("externally validated", phrases)
        self.assertIn("hosted leaderboard-ready", phrases)
        self.assertIn("community benchmark", phrases)

    def test_forbidden_phrase_in_avoid_list_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "readme.md").write_text(
                "Avoid:\n\n- `community benchmark`\n- `externally validated`\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/readme.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root,
                check=True,
                text=True,
            )
            result = _run_check(root)
        self.assertTrue(result["passed"], result)

    def test_forbidden_phrase_in_negated_paragraph_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "readme.md").write_text(
                "This benchmark is not a hosted leaderboard, externally validated\n"
                "benchmark, or community benchmark. See the claim ledger for details.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/readme.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root,
                check=True,
                text=True,
            )
            result = _run_check(root)
        self.assertTrue(result["passed"], result)

    def test_unrelated_nearby_negation_does_not_allow_forbidden_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "readme.md").write_text(
                "No setup required.\n\n"
                "This benchmark is an externally validated community benchmark.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/readme.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root,
                check=True,
                text=True,
            )
            result = _run_check(root)
        self.assertFalse(result["passed"], result)
        phrases = sorted(finding["phrase"] for finding in result["findings"])
        self.assertIn("externally validated", phrases)
        self.assertIn("community benchmark", phrases)

    def test_broad_not_substring_does_not_allow_forbidden_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "readme.md").write_text(
                "This is not just internal; it is an externally validated community benchmark.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/readme.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root,
                check=True,
                text=True,
            )
            result = _run_check(root)
        self.assertFalse(result["passed"], result)
        phrases = sorted(finding["phrase"] for finding in result["findings"])
        self.assertIn("externally validated", phrases)
        self.assertIn("community benchmark", phrases)

    def test_forbidden_phrase_in_forbidden_table_column_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "claim.md").write_text(
                "| Claim | Status | Evidence | Forbidden stronger wording |\n"
                "| --- | --- | --- | --- |\n"
                "| benchmark | supported | evidence | `hosted leaderboard-ready`, `community benchmark` |\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/claim.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root,
                check=True,
                text=True,
            )
            result = _run_check(root)
        self.assertTrue(result["passed"], result)

    def test_forbidden_table_header_does_not_allow_later_plain_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "claim.md").write_text(
                "| Claim | Status | Evidence | Forbidden stronger wording |\n"
                "| --- | --- | --- | --- |\n"
                "| benchmark | supported | evidence | `community benchmark` |\n"
                "\n"
                "This is an externally validated community benchmark.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/claim.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root,
                check=True,
                text=True,
            )
            result = _run_check(root)
        self.assertFalse(result["passed"], result)
        phrases = sorted(finding["phrase"] for finding in result["findings"])
        self.assertIn("externally validated", phrases)
        self.assertIn("community benchmark", phrases)

    def test_check_excludes_panel_logs_and_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "reviews").mkdir(parents=True)
            (root / "docs" / "reviews" / "old.md").write_text(
                "This benchmark is a hosted leaderboard-"
                "ready community "
                "benchmark.\n",
                encoding="utf-8",
            )
            (root / ".handoff").mkdir()
            (root / ".handoff" / "scratch.md").write_text(
                "This benchmark is externally "
                "validated.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "-A"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root,
                check=True,
                text=True,
            )
            result = _run_check(root)
        self.assertTrue(result["passed"], result)

    def test_credible_candidate_claim_is_rejected(self) -> None:
        """A sentence that wraps all three overclaim phrases in
        non-negation soft-language ('credible', 'candidate', etc.) must
        still be rejected. Prior to tightening NEGATION_HINTS, the
        over-broad hints 'candidate', 'credible', 'tier', 'pending',
        'claim boundary', and 'checklist' caused this sentence to be
        incorrectly allowed.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "readme.md").write_text(
                "AuthZBench-SaaS is a credible externally validated "
                "community benchmark candidate.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/readme.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root, check=True, text=True,
            )
            result = _run_check(root)
        self.assertFalse(result["passed"], result)
        phrases = sorted(finding["phrase"] for finding in result["findings"])
        self.assertIn("externally validated", phrases)
        self.assertIn("community benchmark", phrases)

    def test_maturity_label_phrase_still_passes(self) -> None:
        """Tightening NEGATION_HINTS must not block the canonical
        maturity label 'credible v1 internal benchmark' that the
        project uses as the v1 internal release-candidate framing.
        The word 'credible' should be permitted here because the
        sentence does not contain any forbidden phrase in claim
        position.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "readme.md").write_text(
                "AuthZBench-SaaS v1 is a credible internal benchmark "
                "for SaaS authorization reasoning.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/readme.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root, check=True, text=True,
            )
            result = _run_check(root)
        self.assertTrue(result["passed"], result)

    def test_kaggle_platform_acceptance_claims_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "host.md").write_text(
                "AuthZBench-SaaS is Kaggle accepted, Kaggle hosted, "
                "Kaggle leaderboard ready, and platform endorsed.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/host.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root,
                check=True,
                text=True,
            )
            result = _run_check(root)
        self.assertFalse(result["passed"], result)
        phrases = sorted(finding["phrase"] for finding in result["findings"])
        self.assertIn("Kaggle accepted", phrases)
        self.assertIn("Kaggle hosted", phrases)
        self.assertIn("Kaggle leaderboard ready", phrases)
        self.assertIn("platform endorsed", phrases)

    def test_kaggle_platform_non_claims_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "host.md").write_text(
                "This package does not claim `Kaggle accepted`, "
                "`Kaggle hosted`, `Kaggle leaderboard ready`, or "
                "`platform endorsed` status.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/host.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root,
                check=True,
                text=True,
            )
            result = _run_check(root)
        self.assertTrue(result["passed"], result)

    def test_negation_of_different_forbidden_phrase_does_not_allow_current_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "host.md").write_text(
                "This package is not Kaggle accepted. "
                "It is an externally validated benchmark.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/host.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root,
                check=True,
                text=True,
            )
            result = _run_check(root)
        self.assertFalse(result["passed"], result)
        phrases = sorted(finding["phrase"] for finding in result["findings"])
        self.assertIn("externally validated", phrases)

    def test_new_forbidden_phrases_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "host.md").write_text(
                "This benchmark is SaaS-validated and v1.0 released.\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "docs/host.md"], cwd=root, check=True, text=True)
            subprocess.run(
                ["git", "-c", "user.email=test@test", "-c", "user.name=test", "commit", "-m", "init", "-q"],
                cwd=root,
                check=True,
                text=True,
            )
            result = _run_check(root)
        self.assertFalse(result["passed"], result)
        phrases = sorted(finding["phrase"] for finding in result["findings"])
        self.assertIn("SaaS-validated", phrases)
        self.assertIn("v1.0 released", phrases)


if __name__ == "__main__":
    unittest.main()
