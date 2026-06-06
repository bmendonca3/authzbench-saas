from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from authzbench.core import build_context, load_json
from scripts import kiro_live_tool_agent


ROOT = Path(__file__).resolve().parents[1]


class KiroLiveToolAgentTests(unittest.TestCase):
    def test_executes_model_planned_probe_and_submits_live_supported_finding(self) -> None:
        task = load_json(ROOT / "tasks" / "api_tokens" / "tok_cross_tenant_secret_read.json")
        context = build_context(task)
        plan = {
            "probes": [
                {
                    "id": "p1",
                    "actor": "meridian_read_token",
                    "method": "GET",
                    "path": "/api/secrets/{HELIO_SECRET_ID}",
                    "body": None,
                    "purpose": "test cross-tenant secret read",
                }
            ],
            "finding": {
                "claim": "token_cross_tenant_secret_read",
                "boundary": {"attacker_actor": "meridian_read_token", "victim_tenant": "helio"},
                "impact": "read token can access another tenant secret",
                "evidence_probe_id": "p1",
                "out_of_scope_actions": [],
            },
        }

        with patch.object(kiro_live_tool_agent, "run_kiro_plan", return_value=(plan, {"returncode": 0})), patch.object(
            kiro_live_tool_agent,
            "_request",
            return_value={"status": 200, "body": {"secret": {"id": "x"}}},
        ):
            submission, records = kiro_live_tool_agent.solve(context, "claude-sonnet-4.6", 1, 4)

        self.assertEqual(len(submission["findings"]), 1)
        self.assertEqual(
            submission["findings"][0]["evidence"][0]["request"]["path"],
            f"/api/secrets/{context['refs']['HELIO_SECRET_ID']}",
        )
        self.assertEqual(records["artifact"]["executed_probe_count"], 1)

    def test_failed_live_probe_suppresses_model_finding(self) -> None:
        task = load_json(ROOT / "tasks" / "api_tokens" / "tok_cross_tenant_secret_read.json")
        context = build_context(task)
        plan = {
            "probes": [
                {
                    "id": "p1",
                    "actor": "meridian_read_token",
                    "method": "GET",
                    "path": "/api/secrets/{HELIO_SECRET_ID}",
                    "body": None,
                }
            ],
            "finding": {"claim": "token_cross_tenant_secret_read", "evidence_probe_id": "p1"},
        }

        with patch.object(kiro_live_tool_agent, "run_kiro_plan", return_value=(plan, {"returncode": 0})), patch.object(
            kiro_live_tool_agent,
            "_request",
            return_value={"status": 403, "body": {"error": "forbidden"}},
        ):
            submission, records = kiro_live_tool_agent.solve(context, "claude-sonnet-4.6", 1, 4)

        self.assertEqual(submission, {"findings": []})
        self.assertEqual(records["artifact"]["submitted_finding_count"], 0)

    def test_parse_failure_runs_safe_fallback_probe_without_finding(self) -> None:
        task = load_json(ROOT / "tasks" / "project_mgmt" / "pm_same_tenant_read_control.json")
        context = build_context(task)

        with patch.object(
            kiro_live_tool_agent,
            "run_kiro_plan",
            return_value=({"probes": [], "finding": None}, {"returncode": 0, "parse_error": "bad json"}),
        ), patch.object(
            kiro_live_tool_agent,
            "_request",
            return_value={"status": 200, "body": {"task": {"id": "x"}}},
        ) as request:
            submission, records = kiro_live_tool_agent.solve(context, "claude-sonnet-4.6", 1, 4)

        self.assertEqual(submission, {"findings": []})
        self.assertEqual(records["artifact"]["executed_probe_count"], 1)
        self.assertEqual(records["artifact"]["fallback_probe_count"], 1)
        self.assertTrue(records["artifact"]["probes"][0]["fallback"])
        self.assertEqual(request.call_args.args[1]["method"], "GET")

    def test_planner_timeout_runs_safe_fallback_probe_without_finding(self) -> None:
        task = load_json(ROOT / "tasks" / "billing" / "bill_bfla_member_reads_plan_settings.json")
        context = build_context(task)

        with patch.object(
            kiro_live_tool_agent.subprocess,
            "run",
            side_effect=kiro_live_tool_agent.subprocess.TimeoutExpired(["kiro"], 1),
        ), patch.object(
            kiro_live_tool_agent,
            "_request",
            return_value={"status": 200, "body": {"plan": {"id": "x"}}},
        ):
            submission, records = kiro_live_tool_agent.solve(context, "qwen3-coder-next", 1, 4)

        self.assertEqual(submission, {"findings": []})
        self.assertEqual(records["artifact"]["executed_probe_count"], 1)
        self.assertEqual(records["artifact"]["fallback_probe_count"], 1)
        self.assertIn("timed out", records["metadata"]["parse_error"])

    def test_main_writes_submission_plan_and_probe_artifacts(self) -> None:
        task = load_json(ROOT / "tasks" / "api_tokens" / "tok_secure_cross_tenant_secret_control.json")
        context = build_context(task)
        plan = {
            "probes": [
                {
                    "id": "p1",
                    "actor": "meridian_read_token",
                    "method": "GET",
                    "path": "/api/secure/secrets/{HELIO_SECRET_ID}",
                    "body": None,
                }
            ],
            "finding": None,
        }

        with tempfile.TemporaryDirectory() as tmp, patch.object(
            kiro_live_tool_agent,
            "run_kiro_plan",
            return_value=(plan, {"returncode": 0}),
        ), patch.object(
            kiro_live_tool_agent,
            "_request",
            return_value={"status": 403, "body": {"error": "forbidden"}},
        ), patch.dict(
            "os.environ",
            {
                "AUTHZBENCH_CONTEXT": str(Path(tmp) / "context.json"),
                "AUTHZBENCH_SUBMISSION": str(Path(tmp) / "submission.json"),
                "AUTHZBENCH_RUN_ID": "unit-run",
                "AUTHZBENCH_TASK_ID": context["task_id"],
                "AUTHZBENCH_AGENT_ID": "kiro_live_tool_agent",
            },
        ):
            Path(tmp, "context.json").write_text(
                kiro_live_tool_agent.json.dumps(context, indent=2, sort_keys=True),
                encoding="utf-8",
            )

            self.assertEqual(kiro_live_tool_agent.main([]), 0)

            self.assertEqual(load_json(Path(tmp) / "submission.json"), {"findings": []})
            self.assertTrue((Path(tmp) / "model-tool-plan.json").exists())
            self.assertEqual(load_json(Path(tmp) / "tool-probes.json")["executed_probe_count"], 1)


if __name__ == "__main__":
    unittest.main()
