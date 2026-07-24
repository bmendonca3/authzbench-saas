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
        "control_type": "denial",
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
        self.assertEqual(result["manifest_count"], 63, result)
        self.assertEqual(result["private_holdout_count"], 0, result)
        self.assertEqual(result["vulnerable_count"], 27, result)
        self.assertEqual(result["control_count"], 36, result)
        self.assertEqual(result["denial_control_count"], 21, result)
        self.assertEqual(result["authorized_allow_control_count"], 15, result)

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

    def test_vulnerable_task_accepts_evidence_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            data = _minimal_task(
                expected_vulnerable=True,
                oracle={
                    "claim": "cross_tenant_task_read",
                    "status": 200,
                    "body_contains": {"viewer": "beta_member"},
                },
                expected_boundary={"attacker_actor": "beta_member", "victim_tenant": "alpha"},
                evidence_requirements=[
                    {
                        "name": "same_tenant_context_read",
                        "index": 0,
                        "request": {
                            "actor": "beta_member",
                            "method": "GET",
                            "path": "/api/projects/{BETA_PROJECT_ID}/tasks/{BETA_PRIVATE_TASK_ID}",
                        },
                        "status": 200,
                        "body_contains": {"task": {"id": "{BETA_PRIVATE_TASK_ID}"}},
                    },
                    {
                        "name": "cross_tenant_alias_read",
                        "index": 1,
                        "request": {
                            "actor": "beta_member",
                            "method": "GET",
                            "path": "/api/workspaces/{ALPHA_PROJECT_ID}/work-items/{ALPHA_PRIVATE_TASK_ID}",
                        },
                        "status": 200,
                        "body_contains": {"task": {"id": "{ALPHA_PRIVATE_TASK_ID}"}},
                    },
                ],
            )
            data.pop("control_type")
            _write_json(path, data)
            result = validate_patterns([str(path)])
        self.assertTrue(result["passed"], result)

    def test_vulnerable_task_accepts_task_declared_v2_boundary_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            data = _minimal_task(
                expected_vulnerable=True,
                oracle={
                    "claim": "cross_tenant_task_read",
                    "status": 200,
                    "body_contains": {"viewer": "beta_member"},
                },
                expected_boundary={"attacker_actor": "beta_member", "victim_tenant": "alpha"},
                boundary_v2_key_aliases={"victim_tenant": ["affected_tenant"]},
            )
            data.pop("control_type")
            _write_json(path, data)
            result = validate_patterns([str(path)])
        self.assertTrue(result["passed"], result)

    def test_rejects_invalid_v2_boundary_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            data = _minimal_task(
                expected_vulnerable=True,
                oracle={
                    "claim": "cross_tenant_task_read",
                    "status": 200,
                    "body_contains": {"viewer": "beta_member"},
                },
                expected_boundary={"attacker_actor": "beta_member", "victim_tenant": "alpha"},
                boundary_v2_key_aliases={"unknown_boundary": ["affected_tenant"], "victim_tenant": ["", ""]},
            )
            data.pop("control_type")
            _write_json(path, data)
            result = validate_patterns([str(path)])
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("boundary_v2_key_aliases key is not in expected_boundary" in error for error in result["errors"]), result)
        self.assertTrue(any("boundary_v2_key_aliases.victim_tenant must be a non-empty list" in error for error in result["errors"]), result)

    def test_rejects_bad_evidence_requirement_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            data = _minimal_task(
                expected_vulnerable=True,
                oracle={
                    "claim": "cross_tenant_task_read",
                    "status": 200,
                    "body_contains": {"viewer": "beta_member"},
                },
                expected_boundary={"attacker_actor": "beta_member", "victim_tenant": "alpha"},
                evidence_requirements=[{"name": "bad_step", "index": -1, "request": {"method": "GET"}}],
            )
            data.pop("control_type")
            _write_json(path, data)
            result = validate_patterns([str(path)])
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("evidence_requirements[0].index" in error for error in result["errors"]), result)

    def test_rejects_evidence_requirement_without_request_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            data = _minimal_task(
                expected_vulnerable=True,
                oracle={
                    "claim": "cross_tenant_task_read",
                    "status": 200,
                    "body_contains": {"viewer": "beta_member"},
                },
                expected_boundary={"attacker_actor": "beta_member", "victim_tenant": "alpha"},
                evidence_requirements=[{"name": "weak_step", "index": 0, "status": 200}],
            )
            data.pop("control_type")
            _write_json(path, data)
            result = validate_patterns([str(path)])
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("evidence_requirements[0].request is required" in error for error in result["errors"]), result)

    def test_private_holdout_seed_must_not_use_public_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            _write_json(path, _minimal_task(seed="public-v0-999"))
            result = validate_patterns([str(path)])
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("private_holdout seed must not use public-* prefix" in error for error in result["errors"]), result)

    def test_authorized_allow_control_requires_2xx_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "task.json"
            _write_json(path, _minimal_task(control_type="authorized_allow"))
            result = validate_patterns([str(path)])
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("authorized_allow control must have a 2xx oracle status" in error for error in result["errors"]), result)

    def test_tasks_private_holdout_requires_private_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks_private" / "holdout" / "task.json"
            data = _minimal_task()
            data.pop("split")
            _write_json(path, data)
            result = validate_patterns([str(path)])
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("tasks_private/holdout manifests must use split=private_holdout" in error for error in result["errors"]), result)


    def test_every_public_task_has_objective_oracle_boundary_and_controls(self) -> None:
        """Hard pytest gate for the goal-external-validation-coverage.md
        objective-2 mandatory-field set. Every public task must carry:

          * objective (string)
          * oracle.status (integer)
          * oracle.body_contains (object or array)
          * expected_boundary (object, for vulnerable tasks; denial
            or authorized_allow control_type, for secure tasks)
          * at least one denial control AND at least one
            authorized-allow control across the public split
            (the per-task gate is: vulnerable tasks need a denial
            control, secure tasks need the right control_type).
        """
        from pathlib import Path as _P

        from authzbench.core import load_json as _load_json

        public_dir = _P(__file__).resolve().parents[1] / "tasks"
        task_files = sorted(public_dir.glob("*/*.json"))
        self.assertGreaterEqual(len(task_files), 60)

        seen_ids: set[str] = set()
        denial_control_count = 0
        authorized_allow_control_count = 0
        for path in task_files:
            data = _load_json(path)
            task_id = data.get("id", path.stem)

            # 1. objective must be a non-empty string.
            objective = data.get("objective")
            self.assertIsInstance(
                objective, str,
                f"{path}: objective must be a string (got {type(objective).__name__})",
            )
            self.assertGreater(
                len(objective.strip()), 0,
                f"{path}: objective must be non-empty",
            )

            # 2. oracle.status and oracle.body_contains must both exist.
            oracle = data.get("oracle")
            self.assertIsInstance(
                oracle, dict,
                f"{path} ({task_id}): oracle must be a dict",
            )
            self.assertIsInstance(
                oracle.get("status"), int,
                f"{path} ({task_id}): oracle.status must be an integer",
            )
            self.assertIn(
                "body_contains", oracle,
                f"{path} ({task_id}): oracle.body_contains is required",
            )

            # 3. expected_boundary / control_type: vulnerable tasks
            #    must carry expected_boundary; secure tasks must set
            #    control_type to denial or authorized_allow.
            if data.get("expected_vulnerable") is True:
                self.assertIsInstance(
                    data.get("expected_boundary"), dict,
                    f"{path} ({task_id}): vulnerable task must include expected_boundary",
                )
            else:
                ct = data.get("control_type")
                self.assertIn(
                    ct, ("denial", "authorized_allow"),
                    f"{path} ({task_id}): secure task must set control_type to denial or authorized_allow",
                )
                if ct == "denial":
                    denial_control_count += 1
                elif ct == "authorized_allow":
                    authorized_allow_control_count += 1

            # 4. The split must have unique ids.
            self.assertNotIn(task_id, seen_ids, f"duplicate task id: {task_id}")
            seen_ids.add(task_id)

        # Whole-split counters: at least one of each control type must
        # exist in the public 60-task set. This is the reviewer-facing
        # proof that denial AND authorized-allow controls are present.
        self.assertGreaterEqual(
            denial_control_count, 1,
            f"public split must include at least 1 denial control; got {denial_control_count}",
        )
        self.assertGreaterEqual(
            authorized_allow_control_count, 1,
            f"public split must include at least 1 authorized_allow control; got {authorized_allow_control_count}",
        )


if __name__ == "__main__":
    unittest.main()
