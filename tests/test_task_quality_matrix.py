from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import generate_task_quality_matrix


ROOT = Path(__file__).resolve().parents[1]


def _string_literals(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _string_literals(item)
    elif isinstance(value, list):
        for item in value:
            yield from _string_literals(item)


def _sensitive_literal(value: str) -> bool:
    return (
        value.startswith("/api/")
        or value.startswith("synthetic-")
        or "{" in value
        or "}" in value
        or "_ID" in value
        or "_TOKEN" in value
        or "_TENANT" in value
        or "private_note" in value
        or " " in value
        or bool(re.search(r"[0-9a-f]{8,}", value))
    )


class TaskQualityMatrixTests(unittest.TestCase):
    def test_public_matrix_counts_and_public_safe_shape(self) -> None:
        matrix = generate_task_quality_matrix.build_matrix()
        summary = matrix["summary"]
        self.assertEqual(summary["task_count"], 63, summary)
        self.assertEqual(summary["app_count"], 6, summary)
        self.assertEqual(summary["vulnerable_task_count"], 27, summary)
        self.assertEqual(summary["control_task_count"], 36, summary)
        self.assertEqual(summary["denial_control_task_count"], 21, summary)
        self.assertEqual(summary["authorized_allow_control_task_count"], 15, summary)
        self.assertEqual(summary["vulnerable_workflow_evidence_task_count"], 27, summary)
        self.assertEqual(summary["tasks_with_quality_flags"], [], summary)
        self.assertTrue(matrix["source"]["public_safe"])

        task = next(
            item for item in matrix["tasks"] if item["id"] == "pm_multistep_beta_update_then_alpha_alias_read"
        )
        self.assertEqual(task["evidence_requirements_count"], 3, task)
        self.assertEqual(task["replay_proof_status"], "multi_step_evidence_requirements", task)
        support_task = next(
            item
            for item in matrix["tasks"]
            if item["id"] == "sup_multistep_agent_status_then_admin_reassignment"
        )
        self.assertEqual(support_task["evidence_requirements_count"], 3, support_task)
        self.assertEqual(
            support_task["replay_proof_status"],
            "multi_step_evidence_requirements",
            support_task,
        )
        matrix_json = json.dumps(matrix)
        self.assertNotIn('"seed":', matrix_json)
        self.assertNotIn("body_contains", matrix_json)
        self.assertNotIn("/api/", matrix_json)
        self.assertNotIn("ALPHA_", matrix_json)
        self.assertNotIn("BETA_", matrix_json)
        self.assertNotIn("private_note", matrix_json)
        self.assertNotIn("board packet", matrix_json)
        self.assertNotIn("name", json.dumps(task["evidence_requirement_steps"]))
        self.assertTrue(all("path" not in step for step in task["evidence_requirement_steps"]))

    def test_public_matrix_omits_sensitive_manifest_literals_across_all_tasks(self) -> None:
        matrix = generate_task_quality_matrix.build_matrix()
        rendered = json.dumps(matrix, sort_keys=True)
        sensitive_literals: set[str] = set()

        for path in sorted((ROOT / "tasks").glob("*/*.json")):
            task = json.loads(path.read_text(encoding="utf-8"))
            seed = task.get("seed")
            if isinstance(seed, str):
                sensitive_literals.add(seed)
            refs = task.get("refs")
            if isinstance(refs, dict):
                sensitive_literals.update(str(item) for item in refs.values() if isinstance(item, str))
            oracle = task.get("oracle")
            if isinstance(oracle, dict):
                sensitive_literals.update(_string_literals(oracle.get("body_contains")))
            requirements = task.get("evidence_requirements")
            if isinstance(requirements, list):
                for requirement in requirements:
                    if not isinstance(requirement, dict):
                        continue
                    request = requirement.get("request")
                    if isinstance(request, dict):
                        path_template = request.get("path")
                        if isinstance(path_template, str):
                            sensitive_literals.add(path_template)
                        sensitive_literals.update(_string_literals(request.get("body")))
                    sensitive_literals.update(_string_literals(requirement.get("body_contains")))

        for literal in sorted(item for item in sensitive_literals if _sensitive_literal(item)):
            self.assertNotIn(literal, rendered)

    def test_writes_json_and_markdown_outputs(self) -> None:
        matrix = generate_task_quality_matrix.build_matrix()
        with tempfile.TemporaryDirectory() as tmp:
            json_output = Path(tmp) / "matrix.json"
            markdown_output = Path(tmp) / "matrix.md"
            generate_task_quality_matrix.write_outputs(matrix, json_output, markdown_output)
            written = json.loads(json_output.read_text(encoding="utf-8"))
            markdown = markdown_output.read_text(encoding="utf-8")

        self.assertEqual(written["schema_version"], "task-quality-matrix-schema-1")
        self.assertIn("# Task Quality Matrix", markdown)
        self.assertIn("pm_multistep_beta_update_then_alpha_alias_read", markdown)

    def test_main_accepts_outputs_outside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_output = Path(tmp) / "matrix.json"
            markdown_output = Path(tmp) / "matrix.md"
            argv = [
                "generate_task_quality_matrix.py",
                "--json-output",
                str(json_output),
                "--markdown-output",
                str(markdown_output),
            ]
            with patch.object(sys, "argv", argv):
                self.assertEqual(generate_task_quality_matrix.main(), 0)

            self.assertTrue(json_output.exists())
            self.assertTrue(markdown_output.exists())


if __name__ == "__main__":
    unittest.main()
