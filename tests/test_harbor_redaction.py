"""Tests for Harbor adapter redaction and privacy helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench_harbor.redaction import (
    REDACTED_PLACEHOLDER,
    public_safe_task,
    redact_absolute_paths,
    redact_private_fields,
    scan_for_violations,
)
from authzbench_harbor.schemas import check_public_safety


class TestRedactPrivateFields(unittest.TestCase):
    def test_seed_is_redacted(self) -> None:
        data = {"id": "task-1", "seed": "secret-seed-value", "app": "project_mgmt"}
        result = redact_private_fields(data)
        self.assertEqual(result["seed"], REDACTED_PLACEHOLDER)
        self.assertEqual(result["id"], "task-1")
        self.assertEqual(result["app"], "project_mgmt")

    def test_oracle_is_redacted(self) -> None:
        data = {"id": "task-1", "oracle": {"claim": "cross_tenant", "status": 200}}
        result = redact_private_fields(data)
        self.assertEqual(result["oracle"], REDACTED_PLACEHOLDER)

    def test_controls_are_redacted(self) -> None:
        data = {"id": "task-1", "controls": [{"name": "ctrl", "actor": "a", "method": "GET"}]}
        result = redact_private_fields(data)
        self.assertEqual(result["controls"], REDACTED_PLACEHOLDER)

    def test_credential_is_redacted(self) -> None:
        data = {"id": "task-1", "credential": "my-secret-key"}
        result = redact_private_fields(data)
        self.assertEqual(result["credential"], REDACTED_PLACEHOLDER)

    def test_nested_private_fields_are_redacted(self) -> None:
        data = {"id": "task-1", "config": {"seed": "nested-seed", "public": "ok"}}
        result = redact_private_fields(data)
        self.assertEqual(result["config"]["seed"], REDACTED_PLACEHOLDER)
        self.assertEqual(result["config"]["public"], "ok")

    def test_public_fields_are_preserved(self) -> None:
        data = {"id": "task-1", "app": "billing", "expected_vulnerable": True, "objective": "test it"}
        result = redact_private_fields(data)
        self.assertEqual(result["id"], "task-1")
        self.assertEqual(result["app"], "billing")
        self.assertEqual(result["expected_vulnerable"], True)

    def test_list_of_dicts_are_recursively_redacted(self) -> None:
        data = {"findings": [{"seed": "bad", "task_id": "t1"}, {"task_id": "t2"}]}
        result = redact_private_fields(data)
        self.assertEqual(result["findings"][0]["seed"], REDACTED_PLACEHOLDER)
        self.assertEqual(result["findings"][0]["task_id"], "t1")
        self.assertEqual(result["findings"][1]["task_id"], "t2")


class TestRedactAbsolutePaths(unittest.TestCase):
    def test_users_path_is_redacted(self) -> None:
        text = "artifact at /Users/alice/project/output.json"
        result = redact_absolute_paths(text)
        self.assertNotIn("/Users/", result)
        self.assertIn(REDACTED_PLACEHOLDER, result)

    def test_home_path_is_redacted(self) -> None:
        text = "file at /home/ubuntu/data"
        result = redact_absolute_paths(text)
        self.assertNotIn("/home/", result)

    def test_tmp_path_is_redacted(self) -> None:
        text = "temp file at /tmp/harbor-run-1234"
        result = redact_absolute_paths(text)
        self.assertNotIn("/tmp/harbor", result)

    def test_safe_text_unchanged(self) -> None:
        text = "artifact/harbor-dataset/task.toml"
        result = redact_absolute_paths(text)
        self.assertEqual(result, text)


class TestPublicSafeTask(unittest.TestCase):
    def test_public_keys_only(self) -> None:
        task = {
            "id": "task-1",
            "app": "billing",
            "seed": "secret",
            "oracle": {"claim": "x"},
            "controls": [],
            "expected_vulnerable": True,
            "policy": "test only",
            "objective": "find vuln",
            "output_schema": "findings",
            "expected_boundary": {"attacker": "a"},
        }
        result = public_safe_task(task)
        self.assertIn("id", result)
        self.assertIn("app", result)
        self.assertIn("expected_vulnerable", result)
        self.assertNotIn("seed", result)
        self.assertNotIn("oracle", result)
        self.assertNotIn("controls", result)
        self.assertNotIn("expected_boundary", result)


class TestCheckPublicSafety(unittest.TestCase):
    def test_private_path_is_flagged(self) -> None:
        violations = check_public_safety("tasks_private/holdout/task.json")
        self.assertTrue(len(violations) > 0)

    def test_local_absolute_path_is_flagged(self) -> None:
        violations = check_public_safety("path is /Users/alice/work/out.json")
        self.assertTrue(len(violations) > 0)

    def test_credential_word_is_flagged(self) -> None:
        violations = check_public_safety('{"credential": "my-key"}')
        self.assertTrue(len(violations) > 0)

    def test_clean_text_has_no_violations(self) -> None:
        violations = check_public_safety('{"task_id": "pm_task_1", "reward": 1.0, "passed": true}')
        self.assertEqual(violations, [])

    def test_harbor_jobs_dir_flagged(self) -> None:
        violations = check_public_safety("output in harbor-jobs/run-123/result.json")
        self.assertTrue(len(violations) > 0)


class TestScanForViolations(unittest.TestCase):
    def test_dict_with_private_path_fails(self) -> None:
        data = {"path": "tasks_private/holdout/task.json", "passed": True}
        violations = scan_for_violations(data, "test artifact")
        self.assertTrue(len(violations) > 0)

    def test_clean_dict_passes(self) -> None:
        data = {"task_id": "pm_ctrl", "reward": 1.0, "passed": True}
        violations = scan_for_violations(data, "test artifact")
        self.assertEqual(violations, [])

    def test_harbor_jobs_in_dict_fails(self) -> None:
        data = {"log_path": "harbor-jobs/run-123/log.txt"}
        violations = scan_for_violations(data, "test artifact")
        self.assertTrue(len(violations) > 0)


if __name__ == "__main__":
    unittest.main()
