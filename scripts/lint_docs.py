#!/usr/bin/env python
"""Lightweight documentation linter."""

from __future__ import annotations

import re
import sys
from pathlib import Path

DOCS = Path("docs")
REQUIRED = [
    "INDEX.md",
    "CONFIG.md",
    "RAG_PIPELINE.md",
    "SAFETY_GOVERNANCE.md",
    "MODEL_ROUTING.md",
    "PROVENANCE.md",
    "REPORTING.md",
    "EXAMPLE_BANK.md",
    "CONNECTORS.md",
    "DEMO_SCENARIOS.md",
]
LINK_RE = re.compile(r"\[(?:[^\]]+)\]\(([^)]+)\)")


def check_exists() -> list[str]:
    missing = [f for f in REQUIRED if not (DOCS / f).exists()]
    return missing


def check_headings() -> list[str]:
    bad = []
    for f in REQUIRED:
        lines = (DOCS / f).read_text(encoding="utf-8").splitlines()
        if not lines or not lines[0].startswith("#"):
            bad.append(f)
    return bad


def check_links() -> list[str]:
    bad = []
    for f in REQUIRED:
        text = (DOCS / f).read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            link = match.group(1)
            if link.startswith("http"):
                continue
            target = (DOCS / link).resolve()
            if not target.exists():
                bad.append(f"{f}: {link}")
    return bad


def main() -> None:
    errors = []
    if missing := check_exists():
        errors.append("Missing docs: " + ", ".join(missing))
    if bad := check_headings():
        errors.append("Missing headings: " + ", ".join(bad))
    if bad := check_links():
        errors.append("Broken links: " + ", ".join(bad))
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)
    print("docs lint passed")


if __name__ == "__main__":
    main()
