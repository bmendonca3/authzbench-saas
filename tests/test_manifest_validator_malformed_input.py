from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from authzbench.validate_manifests import validate_patterns


ROOT = Path(__file__).resolve().parents[1]


def _valid_manifest() -> dict:
    return {
        "id": "tmp_manifest_shape",
        "app": "project_mgmt",
        "seed": "public-shape-001",
        "expected_vulnerable": False,
        "control_type": "denial",
        "allowed_hosts": ["project_mgmt"],
        "policy": "Temporary malformed-input validation fixture.",
        "objective": "Verify malformed manifests fail closed.",
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


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def _run_cli(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "authzbench.validate_manifests",
            "--task",
            str(path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class MalformedManifestValidationTests(unittest.TestCase):
    def test_non_object_root_returns_bounded_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            _write_json(path, ["not", "an", "object"])
            result = validate_patterns([str(path)])

        self.assertFalse(result["passed"], result)
        self.assertEqual(result["manifest_count"], 1, result)
        self.assertEqual(result["vulnerable_count"], 0, result)
        self.assertEqual(result["control_count"], 0, result)
        self.assertEqual(result["errors"], [f"{path}: manifest root must be an object"])

    def test_invalid_foundational_types_are_aggregated_without_traceback(self) -> None:
        manifest = _valid_manifest()
        manifest.update(
            {
                "id": ["not-hashable"],
                "seed": 123,
                "expected_vulnerable": "false",
                "allowed_hosts": "project_mgmt",
                "oracle": [],
                "controls": ["not-an-object"],
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            _write_json(path, manifest)
            result = validate_patterns([str(path)])

        self.assertFalse(result["passed"], result)
        self.assertEqual(result["vulnerable_count"], 0, result)
        self.assertEqual(result["control_count"], 0, result)
        joined = "\n".join(result["errors"])
        self.assertIn("id must be a non-empty string", joined)
        self.assertIn("seed must be a non-empty string", joined)
        self.assertIn("expected_vulnerable must be a boolean", joined)
        self.assertIn("allowed_hosts must be a non-empty list of strings", joined)
        self.assertIn("oracle must be an object", joined)
        self.assertIn("every controls item must be an object", joined)

    def test_cli_returns_json_and_nonzero_for_non_object_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            _write_json(path, "not-an-object")
            completed = _run_cli(path)

        self.assertEqual(completed.returncode, 1, completed)
        self.assertEqual(completed.stderr, "", completed)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["passed"], payload)
        self.assertEqual(payload["errors"], [f"{path}: manifest root must be an object"])

    def test_unhashable_control_type_returns_bounded_error(self) -> None:
        manifest = _valid_manifest()
        manifest["control_type"] = []
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            _write_json(path, manifest)
            result = validate_patterns([str(path)])
            completed = _run_cli(path)

        expected = f"{path}: secure-control task must set control_type to denial or authorized_allow"
        self.assertFalse(result["passed"], result)
        self.assertIn(expected, result["errors"])
        self.assertEqual(completed.returncode, 1, completed)
        self.assertEqual(completed.stderr, "", completed)
        payload = json.loads(completed.stdout)
        self.assertIn(expected, payload["errors"])

    def test_task_id_cannot_escape_result_directories(self) -> None:
        manifest = _valid_manifest()
        manifest["id"] = "../escaped-task"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            _write_json(path, manifest)
            result = validate_patterns([str(path)])

        self.assertFalse(result["passed"], result)
        self.assertIn(f"{path}: id must be a safe single path component", result["errors"])

    def test_malformed_boundary_alias_contract_returns_bounded_errors(self) -> None:
        manifest = _valid_manifest()
        manifest.update(
            {
                "expected_vulnerable": True,
                "expected_boundary": {"attacker_actor": "beta_member"},
                "boundary_aliases": {
                    "attacker_actor": "beta_member",
                    "unknown_dimension": ["value"],
                },
                "oracle": {
                    "claim": "cross_tenant_read",
                    "status": 200,
                    "body_contains": {"ok": True},
                },
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            _write_json(path, manifest)
            result = validate_patterns([str(path)])

        self.assertFalse(result["passed"], result)
        joined = "\n".join(result["errors"])
        self.assertIn("boundary_aliases.attacker_actor must be a non-empty list of strings", joined)
        self.assertIn("boundary_aliases contains unknown expected boundary key", joined)

    def test_incomplete_oracle_and_control_objects_fail_before_scoring(self) -> None:
        manifest = _valid_manifest()
        manifest["oracle"] = {"claim": "no_vulnerability"}
        manifest["controls"] = [{}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            _write_json(path, manifest)
            result = validate_patterns([str(path)])
            completed = _run_cli(path)

        self.assertFalse(result["passed"], result)
        joined = "\n".join(result["errors"])
        self.assertIn("oracle.status must be an integer", joined)
        self.assertIn("oracle.body_contains must be non-empty", joined)
        for field in ("name", "actor", "method", "path"):
            self.assertIn(f"controls[0].{field} must be a non-empty string", joined)
        self.assertIn("controls[0].status must be an integer", joined)
        self.assertEqual(completed.returncode, 1, completed)
        self.assertEqual(completed.stderr, "", completed)

    def test_deep_template_nesting_returns_json_without_traceback(self) -> None:
        manifest = _valid_manifest()
        nested: object = "value"
        for _ in range(500):
            nested = [nested]
        manifest["oracle"]["body_contains"] = nested
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            _write_json(path, manifest)
            completed = _run_cli(path)

        self.assertEqual(completed.returncode, 1, completed)
        self.assertEqual(completed.stderr, "", completed)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["passed"], payload)
        self.assertIn(
            f"{path}: oracle nesting exceeds validation limit 100",
            payload["errors"],
        )


if __name__ == "__main__":
    unittest.main()
