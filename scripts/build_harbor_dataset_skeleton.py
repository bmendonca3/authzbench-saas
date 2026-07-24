"""Compatibility entrypoint for the packaged Harbor dataset builder."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from authzbench_harbor.dataset_builder import build_harbor_dataset_skeleton, main


__all__ = ["build_harbor_dataset_skeleton", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
