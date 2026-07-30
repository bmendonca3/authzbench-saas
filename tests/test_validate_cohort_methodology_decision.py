from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_cohort_methodology_decision.py"
SPEC = importlib.util.spec_from_file_location("validate_cohort_methodology_decision", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CohortMethodologyDecisionTests(unittest.TestCase):
    def _fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for relative in (
            MODULE.DECISION_PATH,
            MODULE.SCHEMA_PATH,
            MODULE.CONTRACT_PATH,
            *(Path(path) for path in MODULE.SUMMARY_PATHS),
        ):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        return temp, root

    @staticmethod
    def _mutate(root: Path, mutate) -> None:
        path = root / MODULE.DECISION_PATH
        value = json.loads(path.read_text(encoding="utf-8"))
        mutate(value)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_real_pending_decision_passes_structurally(self) -> None:
        result = MODULE.validate(ROOT)
        self.assertTrue(result["passed"], result["errors"])
        self.assertFalse(result["methodology_complete"])

    def test_pending_decision_fails_strict_completion(self) -> None:
        result = MODULE.validate(ROOT, require_complete=True)
        self.assertFalse(result["passed"])
        self.assertIn("cohort methodology decision is pending", result["errors"])

    def test_decision_rejects_duplicate_json_keys(self) -> None:
        temp, root = self._fixture()
        with temp:
            (root / MODULE.DECISION_PATH).write_text(
                '{"schema_version":"cohort-methodology-decision-v1",'
                '"schema_version":"cohort-methodology-decision-v1"}',
                encoding="utf-8",
            )
            result = MODULE.validate(root)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("duplicate JSON key" in error for error in result["errors"]),
            result["errors"],
        )

    def test_contract_digest_drift_fails(self) -> None:
        temp, root = self._fixture()
        with temp:
            contract = root / MODULE.CONTRACT_PATH
            contract.write_text(contract.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            result = MODULE.validate(root)
        self.assertFalse(result["passed"])
        self.assertIn("cohort contract digest is stale", result["errors"])

    def test_public_manifest_digest_mismatch_fails(self) -> None:
        temp, root = self._fixture()
        with temp:
            self._mutate(
                root,
                lambda value: value["source_bindings"].update(
                    {"public_manifest_set_sha256": "0" * 64}
                ),
            )
            result = MODULE.validate(root)
        self.assertFalse(result["passed"])
        self.assertIn(
            "decision public manifest digest does not match cohort contract",
            result["errors"],
        )

    def test_pending_cannot_admit_tasks_or_claim_launch(self) -> None:
        temp, root = self._fixture()
        with temp:
            self._mutate(
                root,
                lambda value: value.update(
                    {
                        "cohort_admitted": True,
                        "admitted_scored_task_count": 48,
                        "launch_ready": True,
                    }
                ),
            )
            result = MODULE.validate(root)
        self.assertFalse(result["passed"])
        self.assertTrue(any("launch_ready" in error for error in result["errors"]))
        self.assertTrue(any("cohort_admitted" in error for error in result["errors"]))

    def test_private_detail_key_fails(self) -> None:
        temp, root = self._fixture()
        with temp:
            self._mutate(root, lambda value: value.update({"private_task_ids": []}))
            result = MODULE.validate(root)
        self.assertFalse(result["passed"])
        self.assertTrue(any("private-detail key" in error for error in result["errors"]))

    def test_accepted_state_requires_source_bound_private_summary_refresh(self) -> None:
        temp, root = self._fixture()
        with temp:
            self._mutate(
                root,
                lambda value: value.update(
                    {
                        "status": "accepted",
                        "reviewer_role_scope": "Independent benchmark methodology reviewer",
                        "review_date": "2026-07-29",
                        "reviewed_commit_sha": "0" * 40,
                        "methodology_decision": "accept",
                        "cohort_admitted": True,
                        "admitted_scored_task_count": 24,
                        "blocker": None,
                        "next_action": None,
                    }
                ),
            )
            result = MODULE.validate(root, require_complete=True)
        self.assertFalse(result["passed"])
        self.assertIn(
            "accepted decision requires current private summary bindings",
            result["errors"],
        )
        self.assertIn(
            "accepted decision requires an existing reviewed commit",
            result["errors"],
        )

    def test_accepted_state_requires_cluster_and_numeric_analysis(self) -> None:
        temp, root = self._fixture()
        with temp:
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.name", "bmendonca3"], cwd=root, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "bmendonca3@example.com"],
                cwd=root,
                check=True,
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
            sha = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            self._mutate(
                root,
                lambda value: value.update(
                    {
                        "status": "accepted",
                        "reviewer_role_scope": "Independent benchmark methodology reviewer",
                        "review_date": "2026-07-29",
                        "reviewed_commit_sha": sha,
                        "methodology_decision": "accept",
                        "cohort_admitted": True,
                        "admitted_scored_task_count": 24,
                        "blocker": None,
                        "next_action": None,
                    }
                ),
            )
            result = MODULE.validate(root, require_complete=True)
        self.assertFalse(result["passed"])
        self.assertTrue(
            any("cluster assignment" in error for error in result["errors"]),
            result["errors"],
        )
        self.assertTrue(
            any("numeric minimum analysis" in error for error in result["errors"]),
            result["errors"],
        )


if __name__ == "__main__":
    unittest.main()
