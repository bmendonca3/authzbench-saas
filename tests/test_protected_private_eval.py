from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from authzbench.core import load_json
from scripts.protected_private_eval import ROOT, redacted_summary, run_protected_private_eval


class ProtectedPrivateEvalTests(unittest.TestCase):
    def test_agent_receives_rendered_context_from_empty_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = load_json(ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json")
            task["id"] = "private_test_same_tenant_read_control"
            task["split"] = "private_holdout"
            task["holdout_variant"] = {"route_variant": "test", "decoy_variant": "test"}
            task_path = tmp_path / "holdout.json"
            task_path.write_text(__import__("json").dumps(task), encoding="utf-8")

            agent_path = tmp_path / "agent.py"
            agent_path.write_text(
                textwrap.dedent(
                    """
                    import json
                    import os
                    from pathlib import Path

                    cwd_entries = [path.name for path in Path.cwd().iterdir()]
                    assert cwd_entries == [], cwd_entries
                    assert not (Path.cwd() / "tasks_private").exists()
                    context = json.loads(Path(os.environ["AUTHZBENCH_CONTEXT"]).read_text())
                    assert "oracle" not in context
                    assert "controls" not in context
                    assert "holdout_variant" not in context
                    assert context["task_id"] == "private_test_same_tenant_read_control"
                    Path(os.environ["AUTHZBENCH_SUBMISSION"]).write_text(
                        json.dumps({"findings": []})
                    )
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            summary = run_protected_private_eval(
                [str(task_path)],
                agent_cmd=f"python3 {agent_path}",
                results_dir=tmp_path / "results",
                timeout_seconds=10,
                benchmark_version="test",
                benchmark_commit_sha="test-sha",
                agent="dummy-agent",
                model="dummy-model",
                harness_type="no-tools-model",
                run_id="test-run",
            )

        self.assertEqual(summary["task_count"], 1, summary)
        self.assertEqual(summary["passed_count"], 1, summary)
        self.assertFalse(summary["protected_execution"]["private_manifests_readable_in_agent_workspace"], summary)
        self.assertEqual(summary["protected_execution"]["agent_received"], "rendered-context-only", summary)

    def test_redacted_summary_omits_task_rows_and_ids(self) -> None:
        summary = {
            "agent": "dummy-agent",
            "authorized_allow_control_task_count": 0,
            "benchmark_commit_sha": "abc123",
            "benchmark_version": "test",
            "control_task_count": 1,
            "denial_control_task_count": 1,
            "harness_type": "no-tools-model",
            "model": "dummy-model",
            "protected_execution": {
                "agent_cwd": "temporary-empty-workspace",
                "agent_received": "rendered-context-only",
                "private_manifests_readable_in_agent_workspace": False,
                "raw_result_bundle_tracked": False,
                "tracked_private_manifest_count": 0,
            },
            "run_id": "private-run",
            "target_request_coverage_rate": None,
            "task_count": 1,
            "tasks": [{"task_id": "private_hidden_task"}],
            "v0_metric_profile": "v0-candidate-authz-evidence",
            "vulnerable_task_count": 0,
        }

        redacted = redacted_summary(summary)

        self.assertNotIn("tasks", redacted)
        self.assertNotIn("private_hidden_task", str(redacted))
        self.assertEqual(redacted["private_holdout_task_count"], 1)
        self.assertTrue(redacted["redacted_private_holdout_source"])


if __name__ == "__main__":
    unittest.main()
