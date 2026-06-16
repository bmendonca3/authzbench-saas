import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from scripts.validate_host_presentation import run_cmd


class ValidateHostPresentationTests(unittest.TestCase):
    @patch("subprocess.run")
    def test_run_cmd_success(self, mock_run: MagicMock) -> None:
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "all good"
        mock_run.return_value = mock_res

        ok, output = run_cmd(["some", "cmd"], Path("."))
        self.assertTrue(ok)
        self.assertEqual(output, "all good")

    @patch("subprocess.run")
    def test_run_cmd_failure(self, mock_run: MagicMock) -> None:
        mock_res = MagicMock()
        mock_res.returncode = 1
        mock_res.stdout = "failed check"
        mock_run.return_value = mock_res

        ok, output = run_cmd(["some", "cmd"], Path("."))
        self.assertFalse(ok)
        self.assertEqual(output, "failed check")
