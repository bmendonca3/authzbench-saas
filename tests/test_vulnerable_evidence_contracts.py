from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from authzbench.core import build_context, load_json, resolve_templates
from authzbench.score import score_submission
from authzbench.validate_manifests import validate_patterns
from scripts.generate_vulnerable_evidence_contracts import (
    EVIDENCE_CONTRACT_VERSION,
    expected_task,
    generate,
)
from scripts.scripted_baseline_agent import solve


ROOT = Path(__file__).resolve().parents[1]
TASK_PATHS = sorted(ROOT.glob("tasks/*/*.json"))


class VulnerableEvidenceContractTests(unittest.TestCase):
    def test_generator_check_is_clean_and_covers_all_vulnerable_tasks(self) -> None:
        result = generate(ROOT)
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["changed_paths"], [])
        self.assertEqual(result["public_task_count"], 63)
        self.assertEqual(result["vulnerable_task_count"], 27)

    def test_all_vulnerable_tasks_have_deny_then_bypass_contracts(self) -> None:
        vulnerable = []
        for path in TASK_PATHS:
            task = load_json(path)
            if task.get("expected_vulnerable") is not True:
                continue
            vulnerable.append(task["id"])
            requirements = task["evidence_requirements"]
            self.assertEqual(
                task["evidence_contract_version"],
                EVIDENCE_CONTRACT_VERSION,
                task["id"],
            )
            self.assertGreaterEqual(len(requirements), 2, task["id"])
            self.assertTrue(
                any(
                    isinstance(item.get("status"), int)
                    and not 200 <= item["status"] < 300
                    for item in requirements[:-1]
                ),
                task["id"],
            )
            self.assertTrue(
                200 <= requirements[-1]["status"] < 300,
                task["id"],
            )
        self.assertEqual(len(vulnerable), 27)

    def test_generator_is_idempotent_and_does_not_change_controls(self) -> None:
        for path in TASK_PATHS:
            task = load_json(path)
            generated = expected_task(task)
            self.assertEqual(generated, task, task["id"])
            if task.get("expected_vulnerable") is not True:
                self.assertIsNot(generated, task)

    def test_scripted_baseline_uses_the_resolved_manifest_chain(self) -> None:
        for path in TASK_PATHS:
            task = load_json(path)
            if task.get("expected_vulnerable") is not True:
                continue
            context = build_context(task)
            submission = solve(context)
            expected = [
                {"request": requirement["request"]}
                for requirement in resolve_templates(
                    task["evidence_requirements"],
                    context["refs"],
                )
            ]
            self.assertEqual(
                submission["findings"][0]["evidence"],
                expected,
                task["id"],
            )

    def test_bypass_only_fails_while_full_chain_passes(self) -> None:
        task = load_json(
            ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json"
        )
        context = build_context(task)
        submission = solve(context)
        full_result = score_submission(task, submission)
        self.assertTrue(full_result["passed"], full_result)
        bypass_only = copy.deepcopy(submission)
        bypass_only["findings"][0]["evidence"] = [
            bypass_only["findings"][0]["evidence"][-1]
        ]
        bypass_result = score_submission(task, bypass_only)
        self.assertFalse(bypass_result["passed"], bypass_result)
        self.assertFalse(bypass_result["evidence_chain_complete"], bypass_result)

    def test_missing_current_manifest_contract_cannot_score_or_promote(self) -> None:
        task = load_json(
            ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json"
        )
        submission = solve(build_context(task))
        variants = {
            "missing_version": {"evidence_contract_version": None},
            "missing_requirements": {"evidence_requirements": None},
        }
        for name, replacements in variants.items():
            with self.subTest(name=name):
                changed = copy.deepcopy(task)
                for field, value in replacements.items():
                    if value is None:
                        changed.pop(field, None)
                    else:
                        changed[field] = value
                result = score_submission(changed, submission)
                self.assertFalse(result["evidence_chain_complete"], result)
                self.assertFalse(result["exploit_proven"], result)
                self.assertEqual(result["subscores"]["exploit_proof"], 0, result)
                self.assertFalse(result["core_passed"], result)
                self.assertFalse(result["promotion_eligible"], result)

    def test_missing_last_extra_or_reordered_chain_step_cannot_pass(self) -> None:
        task = load_json(
            ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json"
        )
        submission = solve(build_context(task))
        evidence = submission["findings"][0]["evidence"]
        variants = {
            "missing_last": evidence[:-1],
            "extra_step": evidence + [copy.deepcopy(evidence[-1])],
            "reordered": list(reversed(evidence)),
        }
        for name, replacement in variants.items():
            with self.subTest(name=name):
                changed = copy.deepcopy(submission)
                changed["findings"][0]["evidence"] = copy.deepcopy(replacement)
                result = score_submission(task, changed)
                self.assertFalse(result["evidence_chain_complete"], result)
                self.assertFalse(result["exploit_proven"], result)
                self.assertFalse(result["core_passed"], result)
                self.assertFalse(result["promotion_eligible"], result)

    def test_manifest_validator_rejects_missing_or_non_denial_chain_contract(self) -> None:
        task = load_json(
            ROOT / "tasks/project_mgmt/pm_bola_read_alpha_from_beta.json"
        )
        variants = {
            "missing_version": lambda value: value.pop(
                "evidence_contract_version"
            ),
            "missing_requirements": lambda value: value.pop(
                "evidence_requirements"
            ),
            "first_step_is_success": lambda value: value[
                "evidence_requirements"
            ][0].update({"status": 200}),
            "last_step_misses_oracle": lambda value: value[
                "evidence_requirements"
            ][-1].update({"status": 403}),
        }
        for name, mutate in variants.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                changed = copy.deepcopy(task)
                mutate(changed)
                path = Path(tmp) / "task.json"
                path.write_text(
                    json.dumps(changed, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                result = validate_patterns([str(path)])
                self.assertFalse(result["passed"], result)


if __name__ == "__main__":
    unittest.main()
