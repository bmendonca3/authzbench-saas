import tempfile
import unittest
from pathlib import Path

from scripts.validate_host_review_docs import validate_host_docs


class ValidateHostReviewDocsTests(unittest.TestCase):
    def test_current_docs_pass(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = validate_host_docs(root)
        self.assertTrue(result["passed"], result)

    def test_missing_doc_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = validate_host_docs(root)
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("Missing required host document" in err for err in result["errors"]))
