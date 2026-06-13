"""Tests for the v1.1-prep multi-step discovery task cohort.

The v1.1-prep cohort is a parallel directory (`tasks_v11_prep/`) that
demonstrates the `multi_step_discovery` task type and the plan-4.2
categories the public 60-task split does not cover, without changing
the public count. The cohort is locked at 3 tasks and is validated
in isolation; it does not enter the v1-readiness gate or the public
baseline summaries.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench.core import build_context, load_json
from authzbench.score import score_submission
from authzbench.validate_manifests import validate_patterns


V11_PREP_GLOB = "tasks_v11_prep/*/*.json"
EXPECTED_IDS = {
    "sup_bfla_viewer_updates_assigned_ticket_status_discovery",
    "bill_bfla_member_disables_export_entitlement_discovery",
    "fs_team_membership_cross_workspace_discovery",
}


def _build_valid_submission(task: dict, refs: dict) -> dict:
    steps = []
    for req in task["evidence_requirements"]:
        path = req["request"]["path"]
        for key, value in refs.items():
            path = path.replace("{" + key + "}", value)
        steps.append({"request": {**req["request"], "path": path}})
    return {
        "findings": [
            {
                "claim": task["oracle"]["claim"],
                "evidence": steps,
                "boundary": task["expected_boundary"],
                "impact": "v1.1-prep multi-step discovery exploit",
            }
        ]
    }


class V11PrepCohortTests(unittest.TestCase):
    def test_v11_prep_directory_has_exactly_three_tasks(self) -> None:
        paths = sorted(ROOT.glob(V11_PREP_GLOB))
        ids = {load_json(p)["id"] for p in paths}
        self.assertEqual(len(paths), 3, f"expected 3 v1.1-prep tasks, got {len(paths)}: {ids}")
        self.assertEqual(ids, EXPECTED_IDS)

    def test_v11_prep_tasks_validate_as_manifests(self) -> None:
        result = validate_patterns([V11_PREP_GLOB])
        self.assertTrue(result.get("passed"), result)
        self.assertEqual(result.get("errors", []), [])

    def test_v11_prep_tasks_carry_multi_step_discovery_difficulty(self) -> None:
        for path in ROOT.glob(V11_PREP_GLOB):
            task = load_json(path)
            self.assertEqual(task.get("difficulty"), "multi_step_discovery", path.name)
            self.assertIn("v11_prep", task.get("tags", []), path.name)
            self.assertGreaterEqual(len(task.get("evidence_requirements", [])), 2, path.name)

    def test_v11_prep_tasks_have_evidence_chain_complete_under_valid_submission(self) -> None:
        for path in ROOT.glob(V11_PREP_GLOB):
            task = load_json(path)
            refs = build_context(task)["refs"]
            submission = _build_valid_submission(task, refs)
            result = score_submission(task, submission)
            self.assertTrue(result["passed"], f"{path.name}: {result['observations']}")
            self.assertTrue(result["exploit_proven"], f"{path.name}: exploit_proven should be true")
            self.assertTrue(
                result["evidence_chain_complete"],
                f"{path.name}: evidence_chain_complete should be true under valid submission",
            )
            self.assertTrue(
                result["control_replay_passed"],
                f"{path.name}: controls should replay successfully",
            )
            self.assertEqual(
                result["subscores"],
                {
                    "exploit_proof": 1,
                    "boundary_reasoning": 1,
                    "false_positive_control": 1,
                    "safety": 1,
                },
                f"{path.name}: subscores should be all-ones under valid submission",
            )

    def test_v11_prep_tasks_reject_wrong_actor_in_exploit_step(self) -> None:
        for path in ROOT.glob(V11_PREP_GLOB):
            task = load_json(path)
            refs = build_context(task)["refs"]
            # Use the discovery step correctly, then submit the exploit step
            # as a different actor.
            wrong_actor_submission = {
                "findings": [
                    {
                        "claim": task["oracle"]["claim"],
                        "evidence": [
                            {
                                "request": {
                                    **task["evidence_requirements"][0]["request"],
                                    "path": task["evidence_requirements"][0]["request"]["path"].format(**refs),
                                    "actor": "atlas_admin",
                                }
                            },
                            {
                                "request": {
                                    **task["evidence_requirements"][1]["request"],
                                    "path": task["evidence_requirements"][1]["request"]["path"].format(**refs),
                                    "actor": "atlas_admin",
                                }
                            },
                        ],
                        "boundary": task["expected_boundary"],
                        "impact": "wrong actor exploit attempt",
                    }
                ]
            }
            result = score_submission(task, wrong_actor_submission)
            self.assertFalse(
                result["exploit_proven"],
                f"{path.name}: exploit_proven should be false when actor is wrong",
            )

    def test_v11_prep_tasks_list_plan_categories(self) -> None:
        for path in ROOT.glob(V11_PREP_GLOB):
            task = load_json(path)
            categories = task.get("plan_categories", [])
            self.assertGreater(len(categories), 0, f"{path.name}: missing plan_categories")
            self.assertIn(
                "multi_step_discovery",
                [
                    tag
                    for tag in [
                        task.get("difficulty"),
                        *task.get("tags", []),
                    ]
                ],
                f"{path.name}: difficulty or tags should reference multi_step_discovery",
            )


if __name__ == "__main__":
    unittest.main()
