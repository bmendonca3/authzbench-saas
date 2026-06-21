from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from authzbench.core import load_json
from scripts.promote_public_baseline_delta import ROOT, promote


PROMOTED_TASK_IDS = {
    "bill_bfla_member_disables_export_entitlement_discovery",
    "fs_team_membership_cross_workspace_discovery",
    "sup_bfla_viewer_updates_assigned_ticket_status_discovery",
}


def _write_summary(path: Path, template: dict, tasks: list[dict], *, run_id: str) -> None:
    summary = dict(template)
    summary["run_id"] = run_id
    summary["task_count"] = len(tasks)
    summary["tasks"] = tasks
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class PromotePublicBaselineDeltaTests(unittest.TestCase):
    def test_promotes_exact_delta_into_current_public_composite(self) -> None:
        template = load_json(ROOT / "baselines" / "scripted-baseline-public-63-summary.json")
        base_tasks = [task for task in template["tasks"] if task["task_id"] not in PROMOTED_TASK_IDS]
        delta_tasks = [task for task in template["tasks"] if task["task_id"] in PROMOTED_TASK_IDS]
        self.assertEqual(len(base_tasks), 60)
        self.assertEqual(len(delta_tasks), 3)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            base_path = tmp_path / "base-60.json"
            delta_path = tmp_path / "delta-3.json"
            output_path = tmp_path / "merged-63.json"
            _write_summary(base_path, template, base_tasks, run_id="base-60")
            _write_summary(delta_path, template, delta_tasks, run_id="delta-3")

            summary = promote(
                base_path,
                delta_path,
                output_path=output_path,
                run_id="merged-63",
                interpretation="synthetic promoted-composite test",
                promotion_annotation="test composite; not a full rerun",
                benchmark_commit_sha="0" * 40,
                expected_base_task_count=60,
                expected_delta_task_ids=PROMOTED_TASK_IDS,
            )

        self.assertEqual(summary["task_count"], 63)
        self.assertEqual(summary["baseline_construction"], "promoted_cohort_delta_merge")
        self.assertTrue(summary["not_full_rerun"])
        self.assertEqual(summary["base_public_task_count"], 60)
        self.assertEqual(summary["delta_public_task_count"], 3)
        self.assertEqual(summary["merged_public_task_count"], 63)
        self.assertEqual(set(summary["delta_task_ids"]), PROMOTED_TASK_IDS)
        self.assertEqual(
            [task["task_id"] for task in summary["tasks"]],
            [task["id"] for _, task in sorted((path.relative_to(ROOT).as_posix(), load_json(path)) for path in (ROOT / "tasks").glob("*/*.json"))],
        )

    def test_rejects_delta_that_is_not_exact_promoted_task_set(self) -> None:
        template = load_json(ROOT / "baselines" / "scripted-baseline-public-63-summary.json")
        base_tasks = [task for task in template["tasks"] if task["task_id"] not in PROMOTED_TASK_IDS]
        bad_delta_tasks = [task for task in template["tasks"] if task["task_id"] in PROMOTED_TASK_IDS][:2]

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            base_path = tmp_path / "base-60.json"
            delta_path = tmp_path / "bad-delta.json"
            output_path = tmp_path / "merged-63.json"
            _write_summary(base_path, template, base_tasks, run_id="base-60")
            _write_summary(delta_path, template, bad_delta_tasks, run_id="bad-delta")

            with self.assertRaisesRegex(ValueError, "missing promoted delta task ids"):
                promote(
                    base_path,
                    delta_path,
                    output_path=output_path,
                    run_id="merged-63",
                    interpretation="synthetic promoted-composite test",
                    promotion_annotation="test composite; not a full rerun",
                    benchmark_commit_sha="0" * 40,
                    expected_base_task_count=60,
                    expected_delta_task_ids=PROMOTED_TASK_IDS,
                )


if __name__ == "__main__":
    unittest.main()
