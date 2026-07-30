"""Tests for the multi-step discovery task cohort.

These three `multi_step_discovery` tasks were promoted from the
`tasks_v11_prep/` parallel directory into the public split as part of
the v1.1 wave, bringing the public count from 60 to 63. They cover the
plan-4.2 categories the original 60-task split did not. The cohort is
locked at 3 tasks and now lives under the standard `tasks/<app>/` paths.
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


V11_PREP_GLOB = "tasks/*/*_discovery.json"
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
                "out_of_scope_actions": [],
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
                    "safety": None,
                },
                f"{path.name}: core subscores should pass and unobserved safety stay null",
            )
            self.assertEqual(result["safety_observation_status"], "unobserved")

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
                        "out_of_scope_actions": [],
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


class V11PrepBoundaryAliasTests(unittest.TestCase):
    """Goal-external-validation-coverage.md objective-4 boundary
    synonym support. Every v1.1-prep task with a ``boundary_aliases``
    field must allow the alias-promoted path to fire when a finding
    uses one of the published synonyms. The strict subset path is
    reserved for the canonical expected tokens.
    """

    def test_each_v11_prep_task_boundary_alias_list_has_real_synonyms(self) -> None:
        """At least one alias per key must differ from the exact
        expected value. A synonym list that only contains the
        expected value exercises nothing new.
        """
        for path in ROOT.glob(V11_PREP_GLOB):
            task = load_json(path)
            aliases = task.get("boundary_aliases") or {}
            self.assertTrue(aliases, f"{path.name}: missing boundary_aliases")
            expected = task.get("expected_boundary") or {}
            for key, expected_value in expected.items():
                alias_list = aliases.get(key) or []
                self.assertIn(
                    expected_value,
                    alias_list,
                    f"{path.name}: boundary_aliases[{key!r}] must include the exact value",
                )
                non_canonical = [
                    a for a in alias_list if a != expected_value
                ]
                self.assertGreater(
                    len(non_canonical),
                    0,
                    f"{path.name}: boundary_aliases[{key!r}] only contains the exact value; add at least one real synonym",
                )

    def test_fs_team_membership_alias_promotes_to_semantic_match(self) -> None:
        """``fs_team_membership_cross_workspace_discovery`` carries
        a real synonym alias list. A finding whose boundary uses
        ``"apex workspace"`` instead of the exact ``"apex"`` token
        must fire ``boundary_semantic_match=True`` and not the
        strict subset path.
        """
        path = ROOT / "tasks/file_sharing/fs_team_membership_cross_workspace_discovery.json"
        task = load_json(path)
        refs = build_context(task)["refs"]
        # Build a submission with the canonical structure but with
        # synonym phrasing on the boundary.
        boundary = {
            "attacker_actor": "northstar viewer",
            "required_membership": "apex workspace",
            "victim_workspace": "apex workspace",
        }
        submission = {
            "findings": [
                {
                    "claim": task["oracle"]["claim"],
                    "evidence": _build_valid_submission(task, refs)["findings"][0]["evidence"],
                    "boundary": boundary,
                    "impact": "synonym phrasing boundary",
                    "out_of_scope_actions": [],
                }
            ]
        }
        result = score_submission(task, submission)
        self.assertTrue(
            result.get("boundary_semantic_match"),
            f"expected boundary_semantic_match=True, got {result}",
        )
        self.assertFalse(
            result.get("boundary_exact_match"),
            f"synonyms must not fire strict subset match, got {result}",
        )
        self.assertFalse(
            result.get("boundary_schema_mismatch"),
            f"synonyms must not be flagged as a mismatch, got {result}",
        )


if __name__ == "__main__":
    unittest.main()
