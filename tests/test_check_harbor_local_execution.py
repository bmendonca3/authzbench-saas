from __future__ import annotations

import unittest
from unittest import mock

from scripts.check_harbor_local_execution import check_harbor_local_execution


class HarborLocalExecutionPreflightTests(unittest.TestCase):
    def test_reports_missing_harbor_without_claiming_execution(self) -> None:
        with mock.patch("scripts.check_harbor_local_execution.shutil.which", return_value=None):
            result = check_harbor_local_execution(
                task_patterns=["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                harbor_command="harbor",
            )

        self.assertEqual(result["schema_version"], "harbor-local-execution-preflight-v1")
        self.assertFalse(result["harbor_cli_found"])
        self.assertTrue(result["generated_skeleton_validated"], result)
        self.assertFalse(result["ready_for_local_harbor_run"])
        self.assertFalse(result["harbor_execution_verified"])
        self.assertIn("not Harbor execution evidence", result["public_claim_boundary"])
        self.assertIn("Harbor CLI/package is not installed or not on PATH", result["blocked_until"])

    def test_reports_ready_for_local_run_when_harbor_is_discoverable(self) -> None:
        with mock.patch("scripts.check_harbor_local_execution.shutil.which", return_value="/usr/local/bin/harbor"):
            result = check_harbor_local_execution(
                task_patterns=["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                harbor_command="harbor",
            )

        self.assertTrue(result["harbor_cli_found"])
        self.assertTrue(result["generated_skeleton_validated"], result)
        self.assertTrue(result["ready_for_local_harbor_run"])
        self.assertFalse(result["harbor_execution_verified"])
        self.assertEqual(result["blocked_until"], [])


if __name__ == "__main__":
    unittest.main()
