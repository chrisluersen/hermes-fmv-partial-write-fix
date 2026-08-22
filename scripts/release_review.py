#!/usr/bin/env python3
"""Review the exact committed repository tree before private publication."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    ".gitattributes",
    ".gitignore",
    "LICENSE",
    "README.md",
    "patches/hermes-fmv-partial-write-fix.patch",
    "provenance.json",
    "scripts/build_patch.py",
    "scripts/release_review.py",
    "scripts/verify_package.py",
}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, capture_output=True
    ).stdout


def main() -> int:
    tracked = {line for line in git("ls-tree", "-r", "--name-only", "HEAD").splitlines() if line}
    provenance = json.loads((ROOT / "provenance.json").read_text(encoding="utf-8"))
    patch_path = ROOT / provenance["patch"]["path"]
    patch = patch_path.read_bytes()
    combined = b"\n".join((ROOT / name).read_bytes() for name in sorted(tracked))

    text = combined.decode("utf-8", errors="replace")
    forbidden = {
        "work-domain marker": re.compile("lm" + "co", re.IGNORECASE),
        "windows user path": re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.IGNORECASE),
        "token-shaped value": re.compile(r"(?:gh[opusr]_|sk-)[A-Za-z0-9_-]{16,}"),
        "credential assignment": re.compile(
            r"(?:token|api[_-]?key|password)\s*[:=]\s*['\"][^'\"]+",
            re.IGNORECASE,
        ),
    }

    checks = {
        "exact tracked member set": tracked == EXPECTED,
        "clean worktree": git("status", "--porcelain") == "",
        "private intended visibility": provenance["publication"]["visibility"] == "private",
        "no upstream submission": provenance["publication"]["upstream_submission"] is False,
        "patch digest bound": hashlib.sha256(patch).hexdigest() == provenance["patch"]["sha256"],
        "patch byte count bound": len(patch) == provenance["patch"]["bytes"],
        "license present": (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License"),
    }
    for label, pattern in forbidden.items():
        checks[f"no {label}"] = pattern.search(text) is None

    failed = [name for name, ok in checks.items() if not ok]
    report = {
        "commit": git("rev-parse", "HEAD").strip(),
        "tree": git("rev-parse", "HEAD^{tree}").strip(),
        "tracked_files": sorted(tracked),
        "checks": checks,
        "patch_sha256": hashlib.sha256(patch).hexdigest(),
    }
    print(json.dumps(report, indent=2))
    print(f"{len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        print("failed categories: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
