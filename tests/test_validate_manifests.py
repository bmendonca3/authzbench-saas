from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from authzbench.validate_manifests import validate_patterns


def _minimal_task(**overrides):
    data = {
        "id": "tmp_private_task",
        "app": "project_mgmt",
        "seed": "private-v0-001",
        "split": "private_holdout",
        "expected_vulnerable": False,
        "allowed_hosts": ["project_mgmt"],
        "policy": "Temporary validation fixture.",
        "objective": "Validate holdout manifest behavior.",
        "output_schema": "Submit findings: [] when no vulnerability is proven.",
        "oracle": {
            "claim": "no_vulnerability",
            "status": 403,
            "body_contains": {"error": "forbidden"},
        },
        "controls": [
            {
                "name": "secure_cross_tenant_denial",
                "actor": "beta_member",
                "method": "GET",
                "path": "/api/secure/projects/{ALPHA_PROJECT_ID}/tasks/{ALPHA_PRIVATE_TASK_ID}",
                "status": 403,
            }
        ],
    }
    data.update(overrides)
    return data


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


class ManifestValidationTests(unittest.TestCase):
    def test_public_manifests_validate(self) -> None:
        result = validate_patterns(["tasks/*/*.json"])
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["manifest_count"], 21, result)
        self.assertEqual(result["private_holdout_count"], 0, result)
        self.assertEqual(result["vulnerable_count"], 9, result)
        self.assertEqual(result["control_count"], 12, result)

    def test_rejects_unresolved_control_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            _write_json(
                path,
                _minimal_task(
                    controls=[
                        {
                            "name": "bad_template",
                            "actor": "beta_member",
                            "method": "GET",
                            "path": "/api/secure/projects/{MISSING_PROJECT_ID}/tasks/{ALPHA_PRIVATE_TASK_ID}",
                            "status": 403,
                        }
                    ]
                ),
            )
            result = validate_patterns([str(path)])
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("unresolved template in controls" in error for error in result["errors"]), result)

    def test_private_holdout_seed_must_not_use_public_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            _write_json(path, _minimal_task(seed="public-v0-999"))
            result = validate_patterns([str(path)])
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("private_holdout seed must not use public-* prefix" in error for error in result["errors"]), result)

    def test_tasks_private_holdout_requires_private_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks_private" / "holdout" / "task.json"
            data = _minimal_task()
            data.pop("split")
            _write_json(path, data)
            result = validate_patterns([str(path)])
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("tasks_private/holdout manifests must use split=private_holdout" in error for error in result["errors"]), result)


if __name__ == "__main__":
    unittest.main()
