from __future__ import annotations

import copy
import unittest

from authzbench.core import load_json
from scripts.generate_benchmark_charts import ROOT, baseline_rows


class BenchmarkChartTests(unittest.TestCase):
    def test_stale_54_tool_agent_chart_row_preserves_target_request_coverage(self) -> None:
        registry = load_json(ROOT / "baselines" / "baseline-registry.json")
        rows = {
            row["id"]: row
            for row in baseline_rows(registry, score_policy_version="score-policy-v1")
        }

        tool_row = rows["kiro-live-tool-agent-sonnet-current-public-54"]

        self.assertEqual(tool_row["harness_type"], "tool-agent")
        self.assertEqual(tool_row["task_count"], 54)
        self.assertEqual(tool_row["target_request_coverage_rate"], 1.0)
        self.assertEqual(tool_row["release_suitability"], "current_public_stale")
        self.assertTrue(tool_row["requires_rerun_before_current_comparison"])

    def test_canonical_gemini_chart_row_is_stale_v2_rescore_evidence(self) -> None:
        registry = load_json(ROOT / "baselines" / "baseline-registry.json")
        rows = {row["id"]: row for row in baseline_rows(registry)}

        gemini_row = rows["agy-gemini-3-1-pro-high-current-public-63"]

        self.assertEqual(gemini_row["label"], "Gemini 3.1 Pro")
        self.assertEqual(gemini_row["release_suitability"], "current_public_stale")
        self.assertTrue(gemini_row["requires_rerun_before_current_comparison"])

    def test_stale_tool_agent_chart_row_preserves_target_request_coverage(self) -> None:
        registry = load_json(ROOT / "baselines" / "baseline-registry.json")
        rows = {
            row["id"]: row
            for row in baseline_rows(registry, score_policy_version="score-policy-v1")
        }

        tool_row = rows["kiro-live-tool-agent-sonnet-current-public-49"]

        self.assertEqual(tool_row["harness_type"], "tool-agent")
        self.assertEqual(tool_row["target_request_coverage_rate"], 1.0)
        self.assertEqual(tool_row["release_suitability"], "current_public_stale")

    def test_chart_rows_do_not_mix_score_policies(self) -> None:
        registry = copy.deepcopy(load_json(ROOT / "baselines" / "baseline-registry.json"))
        entry = next(item for item in registry["baselines"] if item.get("run_artifacts"))
        entry["expected_score_policy_version"] = "score-policy-v2"
        with self.assertRaisesRegex(ValueError, "score policies do not match"):
            baseline_rows(registry)

    def test_chart_rows_are_filtered_to_one_score_policy(self) -> None:
        registry = load_json(ROOT / "baselines" / "baseline-registry.json")
        rows = baseline_rows(
            registry,
            score_policy_version="score-policy-v2-boundary-normalization",
        )
        self.assertTrue(rows)
        self.assertEqual(
            {row["score_policy_version"] for row in rows},
            {"score-policy-v2-boundary-normalization"},
        )

        v2_rows = baseline_rows(registry, score_policy_version="score-policy-v2")
        self.assertEqual(len(v2_rows), 1)
        self.assertEqual(v2_rows[0]["id"], "gemini-2-5-flash-api-policy-v2-1-current-public-63")
        self.assertEqual({row["score_policy_version"] for row in v2_rows}, {"score-policy-v2"})


if __name__ == "__main__":
    unittest.main()
