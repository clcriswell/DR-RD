#!/usr/bin/env python3
"""Guard against heavy top-level imports in UI modules."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

BLOCKED = {
    "pandas",
    "numpy",
    "openpyxl",
    "matplotlib",
    "sklearn",
    "openai",
    "anthropic",
    "google.cloud",
    "playwright",
    "pydantic",
    "pyarrow",
}


class ImportChecker(ast.NodeVisitor):
    def __init__(self, path: Path):
        self.path = path
        self.errors: list[tuple[int, str]] = []

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            name = alias.name
            if self._is_blocked(name):
                self.errors.append((node.lineno, name))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        mod = node.module or ""
        if self._is_blocked(mod):
            self.errors.append((node.lineno, mod))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        pass  # ignore function bodies

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef

    def visit_If(self, node: ast.If) -> None:  # noqa: N802
        if _is_type_checking(node.test):
            return
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_With(self, node: ast.With) -> None:  # noqa: N802
        for stmt in node.body:
            self.visit(stmt)

    def visit_Try(self, node: ast.Try) -> None:  # noqa: N802
        for stmt in node.body + node.orelse + node.finalbody:
            self.visit(stmt)
        for handler in node.handlers:
            for stmt in handler.body:
                self.visit(stmt)

    def _is_blocked(self, name: str) -> bool:
        return any(name == b or name.startswith(b + ".") for b in BLOCKED)


def _is_type_checking(test: ast.expr) -> bool:
    return isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"


def check_file(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(), filename=str(path))
    chk = ImportChecker(path)
    for stmt in tree.body:
        chk.visit(stmt)
    return chk.errors


def main(paths: Iterable[Path]) -> int:
    errors: list[tuple[Path, int, str]] = []
    for path in paths:
        errs = check_file(path)
        errors.extend((path, ln, name) for ln, name in errs)
    if errors:
        for path, ln, name in errors:
            print(f"{path}:{ln}: disallowed import '{name}'")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    ui_paths = list(Path("app").rglob("*.py")) + list(Path("pages").rglob("*.py"))
    raise SystemExit(main(ui_paths))
