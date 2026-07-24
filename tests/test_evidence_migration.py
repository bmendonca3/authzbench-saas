from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from authzbench.evidence_migration import build_rescore_artifact, sha256_file, validate_rescore_artifact


ROOT = Path(__file__).resolve().parents[1]


class EvidenceMigrationTests(unittest.TestCase):
    def test_builds_digest_bound_artifact_without_modifying_sources(self) -> None:
        task_path = next(iter(sorted((ROOT / "tasks").glob("*/*.json"))))
        task = json.loads(task_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            submission_path = root / "submission.json"
            summary_path = root / "summary.json"
            submission_path.write_text(json.dumps({"task_id": task["id"], "findings": []}) + "\n")
            summary_path.write_text(json.dumps({"task_count": 63, "score_policy_version": "score-policy-v1"}) + "\n")
            before = {path: sha256_file(path) for path in (task_path, submission_path, summary_path)}

            artifact = build_rescore_artifact(
                task_path=task_path,
                submission_path=submission_path,
                source_summary_path=summary_path,
            )

            self.assertEqual(validate_rescore_artifact(artifact), [])
            self.assertEqual(artifact["status"], "rescored_from_policy_v1")
            self.assertEqual(artifact["source"]["summary_sha256"], before[summary_path])
            self.assertEqual(before, {path: sha256_file(path) for path in before})

    def test_rejects_missing_submission(self) -> None:
        task_path = next(iter(sorted((ROOT / "tasks").glob("*/*.json"))))
        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "summary.json"
            summary_path.write_text(json.dumps({"task_count": 63, "score_policy_version": "score-policy-v1"}))
            with self.assertRaisesRegex(ValueError, "submission is missing"):
                build_rescore_artifact(
                    task_path=task_path,
                    submission_path=Path(tmp) / "missing.json",
                    source_summary_path=summary_path,
                )

    def test_rejects_non_v1_source(self) -> None:
        task_path = next(iter(sorted((ROOT / "tasks").glob("*/*.json"))))
        task = json.loads(task_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            submission_path = root / "submission.json"
            summary_path = root / "summary.json"
            submission_path.write_text(json.dumps({"task_id": task["id"], "findings": []}))
            summary_path.write_text(json.dumps({"task_count": 63, "score_policy_version": "score-policy-v2"}))
            with self.assertRaisesRegex(ValueError, "must be score-policy-v1"):
                build_rescore_artifact(
                    task_path=task_path,
                    submission_path=submission_path,
                    source_summary_path=summary_path,
                )

    def test_validator_rejects_policy_mixing_and_bad_digest(self) -> None:
        artifact = {
            "schema_version": "wrong",
            "status": "fresh_execution",
            "source_policy_version": "score-policy-v2",
            "target_policy_version": "score-policy-v1",
            "tool_version": "wrong",
            "task_id": "t",
            "source": {"task_sha256": "bad", "submission_sha256": "bad", "summary_sha256": "bad", "summary_task_count": 0},
            "score": {"task_id": "other", "score_policy_version": "score-policy-v1"},
        }
        errors = validate_rescore_artifact(artifact)
        self.assertGreaterEqual(len(errors), 10)


if __name__ == "__main__":
    unittest.main()
