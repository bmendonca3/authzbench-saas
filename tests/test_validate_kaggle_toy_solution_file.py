import tempfile
import unittest
from pathlib import Path

from scripts.validate_kaggle_toy_solution_file import validate_toy_solution


class ValidateKaggleToySolutionFileTests(unittest.TestCase):
    def test_current_toy_solution_passes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        path = root / "platform/kaggle/toy_solution_file.csv"
        result = validate_toy_solution(path)
        self.assertTrue(result["passed"], result)

    def test_invalid_headers_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.csv"
            path.write_text("Id,Usage,expected\n", encoding="utf-8")
            result = validate_toy_solution(path)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Invalid CSV headers" in err for err in result["errors"]))
