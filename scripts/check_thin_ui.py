#!/usr/bin/env python3
"""Ensure app/ui stays free of business logic imports."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "app" / "ui"
FORBIDDEN_PREFIXES = [
    "orchestrators",
    "core",
    "planning",
    "evaluation",
    "dr_rd",
]
FORBIDDEN_MODULES = [
    "openai",
    "anthropic",
    "cohere",
    "google",
    "vertexai",
    "azure",
    "litellm",
]
ALLOWED_PREFIXES = ["app.ui", "utils", "streamlit"]


def _is_stdlib(module: str) -> bool:
    root = module.split(".", 1)[0]
    return root in sys.stdlib_module_names


def _is_allowed(module: str) -> bool:
    if module.startswith("."):
        return True
    if any(module.startswith(p) for p in ALLOWED_PREFIXES):
        return True
    if _is_stdlib(module):
        return True
    return False


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                if any(mod.startswith(p) for p in FORBIDDEN_PREFIXES + FORBIDDEN_MODULES):
                    errors.append(f"{path}:{node.lineno} disallowed import '{mod}'")
                elif not _is_allowed(mod):
                    errors.append(f"{path}:{node.lineno} non-ui import '{mod}'")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("."):
                continue
            if any(module.startswith(p) for p in FORBIDDEN_PREFIXES + FORBIDDEN_MODULES):
                errors.append(f"{path}:{node.lineno} disallowed import '{module}'")
            elif not _is_allowed(module):
                errors.append(f"{path}:{node.lineno} non-ui import '{module}'")
    return errors


def main() -> int:
    errors: list[str] = []
    for path in UI_DIR.rglob("*.py"):
        errors.extend(check_file(path))
    if errors:
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
