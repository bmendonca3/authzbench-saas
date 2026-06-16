import tempfile
import unittest
from pathlib import Path

from scripts.check_markdown_links import check_markdown_links


class CheckMarkdownLinksTests(unittest.TestCase):
    def test_link_check_with_valid_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "doc.md"
            target = root / "target.md"
            target.write_text("content", encoding="utf-8")
            doc.write_text("[link](target.md)", encoding="utf-8")
            result = check_markdown_links([doc])
            self.assertTrue(result["passed"], result)

    def test_link_check_with_broken_link_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "doc.md"
            doc.write_text("[link](non_existent.md)", encoding="utf-8")
            result = check_markdown_links([doc])
            self.assertFalse(result["passed"], result)
            self.assertTrue(any("non_existent.md" in err for err in result["errors"]))
