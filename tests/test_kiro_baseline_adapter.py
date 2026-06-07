from __future__ import annotations

import json
import unittest

from scripts.kiro_baseline_agent import _extract_json


class KiroBaselineAdapterTests(unittest.TestCase):
    def test_extracts_plain_json(self) -> None:
        self.assertEqual(_extract_json('{"findings": []}')["findings"], [])

    def test_extracts_fenced_json(self) -> None:
        text = '```json\n{"findings": [{"claim": "x"}]}\n```'
        self.assertEqual(_extract_json(text)["findings"][0]["claim"], "x")

    def test_extracts_final_findings_after_transcript_json(self) -> None:
        text = (
            "I considered this example shape first: "
            '{"request":{"actor":"demo","method":"GET","path":"/api/x"}}\n'
            "The final submission is:\n"
            '{"findings":[]}'
        )
        self.assertEqual(_extract_json(text)["findings"], [])

    def test_ignores_non_submission_json_prefix_when_later_finding_exists(self) -> None:
        text = '{"request":{"actor":"demo"}}\n{"findings":[{"claim":"ok"}]}'
        self.assertEqual(_extract_json(text)["findings"][0]["claim"], "ok")

    def test_malformed_fenced_json_falls_back_to_later_submission(self) -> None:
        text = "```json\n{broken\n```\nanalysis...\n{\"findings\":[]}"
        self.assertEqual(_extract_json(text)["findings"], [])


if __name__ == "__main__":
    unittest.main()
