#!/usr/bin/env python3
"""Report suspected unused dependencies."""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections.abc import Iterable
from pathlib import Path

IGNORED_DIRS = {"tests", "examples"}


def iter_py_files(dirs: Iterable[Path]) -> Iterable[Path]:
    for base in dirs:
        for path in Path(base).rglob("*.py"):
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            yield path


def collect_imports(files: Iterable[Path]) -> set[str]:
    modules: set[str] = set()
    for file in files:
        try:
            tree = ast.parse(file.read_text())
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    modules.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module.split(".")[0])
    return modules


def parse_requirements(path: Path) -> set[str]:
    pkgs: set[str] = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-e"):
            continue
        pkg = re.split(r"[<>=\[]", line, maxsplit=1)[0]
        pkgs.add(pkg)
    return pkgs


def scan(dirs: Iterable[Path], requirements_file: Path, ignore: set[str]) -> dict:
    imports = collect_imports(iter_py_files(dirs))
    reqs = parse_requirements(requirements_file)
    unused = sorted(pkg for pkg in reqs if pkg not in imports and pkg not in ignore)
    return {"unused_dependencies": unused}


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect unused dependencies.")
    parser.add_argument("--requirements", default=None)
    parser.add_argument("--json-output", default="reports/unused_deps.json")
    parser.add_argument("--ignore", default="", help="Comma separated packages to ignore")
    parser.add_argument("paths", nargs="*", default=["dr_rd", "core", "app"])
    args = parser.parse_args()

    req_file = (
        Path(args.requirements)
        if args.requirements
        else (
            Path("requirements.lock.txt")
            if Path("requirements.lock.txt").exists()
            else Path("requirements.txt")
        )
    )
    ignore = {p.strip() for p in args.ignore.split(",") if p.strip()}
    results = scan([Path(p) for p in args.paths], req_file, ignore)
    out_path = Path(args.json_output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print(f"Unused deps report written to {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
