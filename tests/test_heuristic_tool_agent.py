from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from authzbench.core import build_context, load_json
from scripts import heuristic_tool_agent


ROOT = Path(__file__).resolve().parents[1]


class HeuristicToolAgentTests(unittest.TestCase):
    def test_expands_documented_paths_from_public_refs(self) -> None:
        task = load_json(ROOT / "tasks" / "api_tokens" / "tok_cross_tenant_secret_read.json")
        context = build_context(task)

        paths = heuristic_tool_agent._expand_path("/api/secrets/{SECRET_ID}", context["refs"])

        self.assertIn(f"/api/secrets/{context['refs']['HELIO_SECRET_ID']}", paths)
        self.assertIn(f"/api/secrets/{context['refs']['MERIDIAN_SECRET_ID']}", paths)

    def test_control_wording_submits_empty_findings_but_keeps_probe_artifact(self) -> None:
        task = load_json(ROOT / "tasks" / "api_tokens" / "tok_secure_cross_tenant_secret_control.json")
        context = build_context(task)

        with patch.object(heuristic_tool_agent, "_request", return_value={"status": 403, "body": {"error": "forbidden"}}):
            submission, probes = heuristic_tool_agent.solve(context)

        self.assertEqual(submission, {"findings": []})
        self.assertGreater(len(probes), 0)

    def test_main_writes_submission_and_tool_probe_artifact(self) -> None:
        task = load_json(ROOT / "tasks" / "api_tokens" / "tok_secure_cross_tenant_secret_control.json")
        context = build_context(task)

        with tempfile.TemporaryDirectory() as tmp, patch.object(
            heuristic_tool_agent,
            "_request",
            return_value={"status": 403, "body": {"error": "forbidden"}},
        ), patch.dict(
            "os.environ",
            {
                "AUTHZBENCH_CONTEXT": str(Path(tmp) / "context.json"),
                "AUTHZBENCH_SUBMISSION": str(Path(tmp) / "submission.json"),
                "AUTHZBENCH_RUN_ID": "unit-run",
                "AUTHZBENCH_TASK_ID": context["task_id"],
                "AUTHZBENCH_AGENT_ID": "heuristic_tool_agent",
            },
        ):
            Path(tmp, "context.json").write_text(
                heuristic_tool_agent.json.dumps(context, indent=2, sort_keys=True),
                encoding="utf-8",
            )

            self.assertEqual(heuristic_tool_agent.main(), 0)

            self.assertTrue(Path(tmp, "submission.json").exists())
            probe_artifact = Path(tmp, "tool-probes.json")
            self.assertTrue(probe_artifact.exists())
            self.assertGreater(load_json(probe_artifact)["probe_count"], 0)


if __name__ == "__main__":
    unittest.main()
