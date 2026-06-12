from __future__ import annotations

import argparse

from .core import build_context, dump_json, load_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a task with concrete seeded IDs.")
    parser.add_argument("task", help="Path to a task JSON manifest")
    args = parser.parse_args()
    print(dump_json(build_context(load_json(args.task))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

