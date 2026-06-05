from __future__ import annotations

import unittest

from authzbench.validate_manifests import validate_patterns


class ManifestValidationTests(unittest.TestCase):
    def test_public_manifests_validate(self) -> None:
        result = validate_patterns(["tasks/*/*.json"])
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["manifest_count"], 12, result)
        self.assertEqual(result["private_holdout_count"], 0, result)
        self.assertEqual(result["vulnerable_count"], 5, result)
        self.assertEqual(result["control_count"], 7, result)


if __name__ == "__main__":
    unittest.main()
