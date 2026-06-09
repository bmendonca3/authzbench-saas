from __future__ import annotations

import subprocess
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

    def test_cli_discovery_does_not_claim_ready_without_real_execution(self) -> None:
        with (
            mock.patch("scripts.check_harbor_local_execution.shutil.which", return_value="/usr/local/bin/harbor"),
            mock.patch("scripts.check_harbor_local_execution.subprocess.run"),
        ):
            result = check_harbor_local_execution(
                task_patterns=["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                harbor_command="harbor",
            )

        self.assertTrue(result["harbor_cli_found"])
        self.assertTrue(result["generated_skeleton_validated"], result)
        self.assertFalse(result["ready_for_local_harbor_run"])
        self.assertFalse(result["harbor_execution_verified"])
        self.assertEqual(result["blocked_until"], ["real Harbor execution has not been run by this preflight"])
        self.assertIn("run -c run_authzbench_saas.yaml --yes", result["local_run_template"])

    def test_command_discovery_uses_executable_from_compound_command(self) -> None:
        with (
            mock.patch("scripts.check_harbor_local_execution.shutil.which") as which,
            mock.patch("scripts.check_harbor_local_execution.subprocess.run") as run,
        ):
            which.return_value = "/usr/local/bin/uvx"
            result = check_harbor_local_execution(
                task_patterns=["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                harbor_command="uvx harbor",
            )

        which.assert_called_once_with("uvx")
        run.assert_called_once()
        self.assertTrue(result["harbor_cli_found"], result)
        self.assertIn("uvx harbor run -c run_authzbench_saas.yaml --yes", result["local_run_template"])

    def test_default_discovery_does_not_treat_broken_uvx_harbor_as_harbor(self) -> None:
        def fake_which(executable: str) -> str | None:
            return "/usr/local/bin/uvx" if executable == "uvx" else None

        with (
            mock.patch("scripts.check_harbor_local_execution.shutil.which", side_effect=fake_which),
            mock.patch("scripts.check_harbor_local_execution.subprocess.run") as run,
        ):
            run.side_effect = subprocess.CalledProcessError(1, ["uvx", "harbor", "--version"])
            result = check_harbor_local_execution(
                task_patterns=["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                harbor_command="harbor",
            )

        run.assert_called_once()
        self.assertFalse(result["harbor_cli_found"], result)
        self.assertEqual(result["harbor_command"], "harbor")
        self.assertIn("Harbor CLI/package is not installed or not on PATH", result["blocked_until"])

    def test_default_discovery_falls_back_to_runnable_uvx_harbor(self) -> None:
        def fake_which(executable: str) -> str | None:
            return "/usr/local/bin/uvx" if executable == "uvx" else None

        with (
            mock.patch("scripts.check_harbor_local_execution.shutil.which", side_effect=fake_which),
            mock.patch("scripts.check_harbor_local_execution.subprocess.run") as run,
        ):
            result = check_harbor_local_execution(
                task_patterns=["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                harbor_command="harbor",
            )

        run.assert_called_once()
        self.assertTrue(result["harbor_cli_found"], result)
        self.assertEqual(result["harbor_command"], "uvx harbor")
        self.assertEqual(result["blocked_until"], ["real Harbor execution has not been run by this preflight"])

    def test_can_skip_harbor_discovery_for_deterministic_public_fixtures(self) -> None:
        with mock.patch("scripts.check_harbor_local_execution.shutil.which", return_value="/usr/local/bin/harbor"):
            result = check_harbor_local_execution(
                task_patterns=["tasks/project_mgmt/pm_same_tenant_read_control.json"],
                harbor_command="harbor",
                discover_harbor_cli=False,
            )

        self.assertFalse(result["harbor_cli_found"])
        self.assertFalse(result["ready_for_local_harbor_run"])
        self.assertIn("Harbor CLI/package is not installed or not on PATH", result["blocked_until"])


if __name__ == "__main__":
    unittest.main()
