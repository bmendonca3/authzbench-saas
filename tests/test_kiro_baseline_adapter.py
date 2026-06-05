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


if __name__ == "__main__":
    unittest.main()

