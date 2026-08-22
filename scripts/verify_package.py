#!/usr/bin/env python3
"""Verify patch-kit integrity without modifying a Hermes checkout."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "provenance.json"


def main() -> int:
    data = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    patch = ROOT / data["patch"]["path"]
    payload = patch.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()

    checks = {
        "patch exists": patch.is_file(),
        "patch sha256": digest == data["patch"]["sha256"],
        "patch bytes": len(payload) == data["patch"]["bytes"],
        "five changed files": len(data["patch"]["changed_files"]) == 5,
        "private publication": data["publication"]["visibility"] == "private",
        "not upstreamed": data["publication"]["upstream_submission"] is False,
    }

    text_files = [
        p for p in ROOT.rglob("*")
        if p.is_file() and ".git" not in p.parts and p.suffix.lower() not in {".png", ".jpg", ".zip"}
    ]
    combined = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in text_files)
    forbidden = {
        # Split environment-specific literals so the scanner does not match
        # its own rule source. A generic ``e`` + six digits rule is omitted:
        # it produces false positives inside SHA-256 and commit hashes.
        "work-domain marker": re.compile("lm" + "co", re.IGNORECASE),
        "windows user path": re.compile(r"[A-Za-z]:[\\/]Users[\\/]", re.IGNORECASE),
        "credential assignment": re.compile(r"(?:token|api[_-]?key|password)\s*[:=]\s*['\"][^'\"]+", re.IGNORECASE),
    }
    for label, pattern in forbidden.items():
        checks[f"no {label}"] = pattern.search(combined) is None

    failed = [name for name, ok in checks.items() if not ok]
    print(json.dumps({"checks": checks, "patch_sha256": digest, "files_scanned": len(text_files)}, indent=2))
    print(f"{len(checks) - len(failed)}/{len(checks)} checks passed")
    if failed:
        print("failed categories: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
