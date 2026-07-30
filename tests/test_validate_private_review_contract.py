from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_private_review_contract.py"
SPEC = importlib.util.spec_from_file_location("validate_private_review_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PrivateReviewContractTests(unittest.TestCase):
    def _copy_fixture(self, target: Path) -> None:
        for relative in [
            ".gitignore",
            MODULE.PUBLIC_SCHEMA,
            MODULE.PRIVATE_SCHEMA,
            MODULE.AGGREGATE_SCHEMA,
            MODULE.EXTERNAL_REGISTRY,
        ]:
            source = ROOT / relative
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())

    def _mutate_json(self, root: Path, relative: Path, mutate) -> None:
        path = root / relative
        value = json.loads(path.read_text(encoding="utf-8"))
        mutate(value)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_real_contract_passes(self) -> None:
        result = MODULE.validate_contract(ROOT)
        self.assertTrue(result["passed"], result["errors"])

    def test_public_schema_cannot_accept_private_pack_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)
            self._mutate_json(
                root,
                MODULE.PUBLIC_SCHEMA,
                lambda value: value["properties"]["pack_id"].update(
                    {"enum": ["public", "active-private-pack"]}
                ),
            )
            result = MODULE.validate_contract(root, check_git=False)
            self.assertFalse(result["passed"])
            self.assertTrue(any("only pack_id='public'" in error for error in result["errors"]))

    def test_registry_cannot_reference_private_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)

            def mutate(value) -> None:
                value["lanes"][0]["schema"] = str(MODULE.PRIVATE_SCHEMA)

            self._mutate_json(root, MODULE.EXTERNAL_REGISTRY, mutate)
            result = MODULE.validate_contract(root, check_git=False)
            self.assertFalse(result["passed"])
            self.assertTrue(any("public AppSec schema" in error for error in result["errors"]))

    def test_registry_rejects_private_pack_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)

            def mutate(value) -> None:
                value["lanes"][0]["per_task_records"] = [
                    {"pack_id": "active-private-pack", "task_id": "private-task"}
                ]

            self._mutate_json(root, MODULE.EXTERNAL_REGISTRY, mutate)
            result = MODULE.validate_contract(root, check_git=False)
            self.assertFalse(result["passed"])
            self.assertTrue(any("pack_id='public'" in error for error in result["errors"]))

    def test_aggregate_schema_cannot_expose_private_task_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)

            def mutate(value) -> None:
                value["properties"]["task_ids"] = {
                    "type": "array",
                    "items": {"type": "string"},
                }

            self._mutate_json(root, MODULE.AGGREGATE_SCHEMA, mutate)
            result = MODULE.validate_contract(root, check_git=False)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any("forbidden private properties" in error for error in result["errors"])
            )

    def test_controlled_response_prefix_must_be_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)
            gitignore = root / ".gitignore"
            gitignore.write_text(
                "\n".join(
                    line
                    for line in gitignore.read_text(encoding="utf-8").splitlines()
                    if line.strip() != MODULE.CONTROLLED_PREFIX
                )
                + "\n",
                encoding="utf-8",
            )
            result = MODULE.validate_contract(root, check_git=False)
            self.assertFalse(result["passed"])
            self.assertTrue(any("must ignore" in error for error in result["errors"]))

    def test_public_registry_rejects_nonfinite_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._copy_fixture(root)
            (root / MODULE.EXTERNAL_REGISTRY).write_text(
                '{"schema_version":"external-review-registry-v1",'
                '"description":Infinity,"lanes":[]}',
                encoding="utf-8",
            )
            result = MODULE.validate_contract(root, check_git=False)
            self.assertFalse(result["passed"])
            self.assertTrue(
                any("non-finite JSON number" in error for error in result["errors"]),
                result["errors"],
            )


if __name__ == "__main__":
    unittest.main()
