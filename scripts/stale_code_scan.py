#!/usr/bin/env python3
"""Detect potentially stale Python modules and files."""

from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

import yaml

IGNORED_DIRS = {"tests", "examples"}


def iter_py_files(dirs: Iterable[Path]) -> Iterable[Path]:
    for base in dirs:
        for path in Path(base).rglob("*.py"):
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            yield path


def module_name_from_path(path: Path, root: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def build_import_graph(
    files: Iterable[Path], root: Path
) -> tuple[dict[Path, set[Path]], dict[str, Path]]:
    module_map: dict[str, Path] = {}
    graph: dict[Path, set[Path]] = defaultdict(set)
    for file in files:
        mod_name = module_name_from_path(file, root)
        module_map[mod_name] = file
    for file in files:
        try:
            tree = ast.parse(file.read_text())
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    base = n.name.split(".")[0]
                    if base in module_map:
                        graph[module_map[base]].add(file)
            elif isinstance(node, ast.ImportFrom) and node.module:
                base = node.module.split(".")[0]
                if base in module_map:
                    graph[module_map[base]].add(file)
    return graph, module_map


def load_repo_map(repo_map_path: str) -> set[str]:
    try:
        data = yaml.safe_load(Path(repo_map_path).read_text())
    except FileNotFoundError:
        return set()
    modules = set()
    for mod in data.get("modules", []):
        path = mod.get("path") if isinstance(mod, dict) else mod
        modules.add(Path(path).as_posix())
    return modules


def find_empty_packages(dirs: Iterable[Path], root: Path) -> list[str]:
    empty: list[str] = []
    for base in dirs:
        for init in Path(base).rglob("__init__.py"):
            if any(part in IGNORED_DIRS for part in init.parts):
                continue
            pkg_dir = init.parent
            py_files = [p for p in pkg_dir.glob("*.py") if p.name != "__init__.py"]
            if not py_files:
                empty.append(pkg_dir.relative_to(root).as_posix())
    return empty


def scan(dirs: Iterable[Path], repo_map_path: str, root: Path = Path(".")) -> dict[str, list[str]]:
    files = list(iter_py_files(dirs))
    graph, module_map = build_import_graph(files, root)
    incoming: dict[Path, int] = defaultdict(int)
    for _src, targets in graph.items():
        for tgt in targets:
            incoming[tgt] += 1
    repo_modules = load_repo_map(repo_map_path)
    unreferenced: list[str] = []
    for _mod_name, path in module_map.items():
        rel = path.relative_to(root).as_posix()
        if rel in repo_modules and incoming[path] == 0:
            unreferenced.append(rel)
    orphans = [
        p.relative_to(root).as_posix()
        for p in files
        if p.relative_to(root).as_posix() not in repo_modules
    ]
    empty_packages = find_empty_packages(dirs, root)
    return {
        "unreferenced_modules": sorted(unreferenced),
        "orphan_files": sorted(orphans),
        "empty_packages": sorted(empty_packages),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect potentially stale code.")
    parser.add_argument("--json-output", default="reports/stale_code.json")
    parser.add_argument("--repo-map", default="repo_map.yaml")
    parser.add_argument("paths", nargs="*", default=["dr_rd", "core", "app"])
    args = parser.parse_args()

    root = Path(".")
    results = scan([Path(p) for p in args.paths], args.repo_map, root)
    out_path = Path(args.json_output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print(f"Stale code scan written to {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
