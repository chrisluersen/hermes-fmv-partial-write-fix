#!/usr/bin/env python3
"""Build a deterministic git-applyable patch from two Hermes source trees."""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path

FILES = (
    "agent/tool_result_classification.py",
    "agent/tool_dispatch_helpers.py",
    "run_agent.py",
    "tests/agent/test_tool_result_classification.py",
    "tests/run_agent/test_file_mutation_verifier.py",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("modified", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    chunks: list[str] = []
    for relative in FILES:
        before = (args.baseline / relative).read_text(encoding="utf-8").splitlines()
        after = (args.modified / relative).read_text(encoding="utf-8").splitlines()
        diff = difflib.unified_diff(
            before,
            after,
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
            lineterm="",
        )
        chunks.extend(f"{line}\n" for line in diff)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(chunks), encoding="utf-8", newline="\n")
    print(f"wrote {args.output} ({args.output.stat().st_size} bytes; {len(FILES)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
