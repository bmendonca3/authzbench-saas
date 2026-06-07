from __future__ import annotations

import unittest

from authzbench.core import load_json
from scripts.generate_benchmark_charts import ROOT, baseline_rows


class BenchmarkChartTests(unittest.TestCase):
    def test_stale_tool_agent_chart_row_preserves_target_request_coverage(self) -> None:
        registry = load_json(ROOT / "baselines" / "baseline-registry.json")
        rows = {row["id"]: row for row in baseline_rows(registry)}

        tool_row = rows["kiro-live-tool-agent-sonnet-current-public-49"]

        self.assertEqual(tool_row["harness_type"], "tool-agent")
        self.assertEqual(tool_row["target_request_coverage_rate"], 1.0)
        self.assertEqual(tool_row["release_suitability"], "current_public_stale")


if __name__ == "__main__":
    unittest.main()
