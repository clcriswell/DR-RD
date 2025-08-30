"""Prompt versioning helpers."""
from __future__ import annotations

from typing import Iterable
import difflib


def next_version(cur: str, part: str) -> str:
    major, minor, patch = [int(x) for x in cur.split('.')]
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def is_upgrade(old: str, new: str) -> bool:
    return tuple(map(int, new.split('.'))) > tuple(map(int, old.split('.')))


def unified_diff(old_text: str, new_text: str) -> str:
    return "".join(difflib.unified_diff(old_text.splitlines(True), new_text.splitlines(True)))

