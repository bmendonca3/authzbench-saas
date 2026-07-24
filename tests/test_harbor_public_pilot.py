from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from authzbench.core import load_json
from authzbench.score import score_submission
from authzbench_harbor.dataset_builder import build_harbor_dataset_skeleton
from authzbench_harbor.public_pilot import (
    PUBLIC_PILOT_TASKS,
    build_public_pilot_reference_submission,
)
from scripts.validate_harbor_dataset_skeleton import validate_harbor_dataset_skeleton


PILOT_PATHS = {
    "tok_cross_tenant_secret_read": "tasks/api_tokens/tok_cross_tenant_secret_read.json",
    "tok_secure_export_scope_control": "tasks/api_tokens/tok_secure_export_scope_control.json",
    "tok_export_token_reads_export_control": "tasks/api_tokens/tok_export_token_reads_export_control.json",
}


class HarborPublicPilotTests(unittest.TestCase):
    def test_reference_submissions_score_one_deterministically(self) -> None:
        self.assertEqual(set(PILOT_PATHS), set(PUBLIC_PILOT_TASKS))
        for task_id, path in PILOT_PATHS.items():
            with self.subTest(task_id=task_id):
                task = load_json(path)
                first = build_public_pilot_reference_submission(task)
                second = build_public_pilot_reference_submission(task)
                self.assertEqual(first, second)
                score = score_submission(
                    task,
                    first,
                    require_control_verification=task["expected_vulnerable"] is False,
                )
                self.assertEqual(score["score"], 1.0, score)
                self.assertTrue(score["passed"], score)
                if task["expected_vulnerable"] is False:
                    self.assertTrue(first["verification"])
                    self.assertTrue(score["control_replay_passed"], score)
                    self.assertTrue(score["control_verification_passed"], score)

    def test_control_reference_requires_participant_selected_verification(self) -> None:
        task = load_json(PILOT_PATHS["tok_secure_export_scope_control"])

        score = score_submission(task, {"findings": []}, require_control_verification=True)

        self.assertEqual(score["score"], 0)
        self.assertFalse(score["passed"], score)
        self.assertFalse(score["control_verification_passed"], score)

    def test_vulnerable_reference_rejects_wrong_actor_and_boundary(self) -> None:
        task = load_json(PILOT_PATHS["tok_cross_tenant_secret_read"])
        submission = build_public_pilot_reference_submission(task)
        forged = copy.deepcopy(submission)
        forged["findings"][0]["boundary"]["attacker_actor"] = "meridian_export_token"
        forged["findings"][0]["evidence"][0]["request"]["actor"] = "meridian_export_token"

        score = score_submission(task, forged)

        self.assertLess(score["score"], 1.0, score)
        self.assertFalse(score["passed"], score)

    def test_builder_emits_three_behavior_contract_and_opaque_contexts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "pilot"
            manifest = build_harbor_dataset_skeleton(
                ["tasks/api_tokens/*.json"],
                output,
                task_ids=list(PILOT_PATHS),
                oracle_solution_mode="public-pilot-reference",
            )
            validation = validate_harbor_dataset_skeleton(output)
            generated = {}
            for entry in manifest["tasks"]:
                task_dir = output / entry["harbor_task_dir"]
                context = json.loads((task_dir / "environment" / "context.json").read_text(encoding="utf-8"))
                solution = (task_dir / "solution" / "solve.sh").read_text(encoding="utf-8")
                task_toml = (task_dir / "task.toml").read_text(encoding="utf-8")
                environment_dockerfile = (task_dir / "environment" / "Dockerfile").read_text(encoding="utf-8")
                verifier_dockerfile = (task_dir / "tests" / "Dockerfile").read_text(encoding="utf-8")
                verifier_script = (task_dir / "tests" / "test.sh").read_text(encoding="utf-8")
                generated[entry["id"]] = (
                    entry,
                    context,
                    solution,
                    task_toml,
                    environment_dockerfile,
                    verifier_dockerfile,
                    verifier_script,
                )

        self.assertTrue(validation["passed"], validation)
        self.assertEqual(set(generated), set(PILOT_PATHS))
        self.assertEqual({item[0]["pilot_behavior"] for item in generated.values()}, set(PUBLIC_PILOT_TASKS.values()))
        for task_id, (
            entry,
            context,
            solution,
            task_toml,
            environment_dockerfile,
            verifier_dockerfile,
            verifier_script,
        ) in generated.items():
            with self.subTest(task_id=task_id):
                self.assertEqual(entry["expected_nop_reward"], 0.0)
                self.assertEqual(entry["expected_oracle_reward"], 1.0)
                self.assertTrue(context["task_id"].startswith("case-"))
                self.assertNotEqual(context["task_id"], task_id)
                self.assertEqual(context["context_profile"], "blinded-evaluation-v1")
                self.assertNotIn("expected_vulnerable", json.dumps(context))
                self.assertNotIn("exit 64", solution)
                self.assertIn("deterministic public-pilot Oracle submission", solution)
                self.assertIn("expected_nop_reward = 0.0", task_toml)
                self.assertIn("expected_oracle_reward = 1.0", task_toml)
                self.assertIn('exec /bin/sh "$@"', environment_dockerfile)
                self.assertIn('exec /bin/sh "$@"', verifier_dockerfile)
                self.assertIn("/logs/verifier/score.json", verifier_script)
                self.assertIn("/logs/verifier/ctrf.json", verifier_script)
                self.assertIn("'results': {", verifier_script)

    def test_pilot_mode_rejects_non_admitted_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "not admitted to the public Harbor pilot"):
                build_harbor_dataset_skeleton(
                    ["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                    Path(tmp) / "pilot",
                    oracle_solution_mode="public-pilot-reference",
                )


if __name__ == "__main__":
    unittest.main()
