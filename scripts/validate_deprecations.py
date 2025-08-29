from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DOC = Path("docs/DEPRECATION_MAP.md")


def parse_map() -> set[str]:
    components: set[str] = set()
    if not DOC.exists():
        return components
    for line in DOC.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and not line.startswith("| component") and "---" not in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells:
                components.add(cells[0])
    return components


def scan_sources() -> set[str]:
    missing: set[str] = set()
    components = parse_map()
    for path in Path(".").rglob("*.py"):
        if path.parts[0] in {".git", "venv"}:
            continue
        text = path.read_text(encoding="utf-8")
        for agent in re.findall(r"warn_legacy_agent_use\(([\"'])([^\"']+)\1", text):
            name = agent[1]
            if name not in components:
                missing.add(name)
        if "@deprecated" in text:
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if "@deprecated" in line and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith("def ") or next_line.startswith("class "):
                        name = next_line.split()[1].split("(")[0]
                        if name not in components:
                            missing.add(name)
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate deprecation coverage")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    missing = scan_sources()
    if missing:
        print("Missing deprecation map entries for:")
        for m in sorted(missing):
            print(f"  - {m}")
        if args.strict:
            sys.exit(1)
    else:
        print("All deprecations documented.")


if __name__ == "__main__":
    main()
