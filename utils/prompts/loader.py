"""Load and validate prompt registry YAML files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List
import yaml
import hashlib
import string

_PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"
_CACHE: Dict[str, dict] | None = None

_ALLOWED_KEYS = {"id", "version", "title", "description", "vars", "template", "changelog"}


def load_all() -> Dict[str, dict]:
    """Load and cache all prompt YAML files."""
    global _CACHE
    if _CACHE is None:
        _CACHE = {}
        for p in _PROMPT_DIR.glob("*.yaml"):
            with p.open("r", encoding="utf-8") as fh:
                obj = yaml.safe_load(fh) or {}
            problems = validate(obj)
            if problems:
                raise ValueError(f"Invalid prompt {p.name}: {problems}")
            _CACHE[obj["id"]] = obj
    return dict(_CACHE)


def load(id_: str) -> dict:
    data = load_all()
    if id_ not in data:
        raise KeyError(id_)
    return data[id_]


def hash_prompt(obj: dict) -> str:
    """Return SHA256 over normalized YAML subset."""
    sub = {k: obj.get(k) for k in ("id", "version", "template", "vars")}
    text = yaml.safe_dump(sub, sort_keys=True).encode("utf-8")
    return hashlib.sha256(text).hexdigest()


def _extract_fields(tmpl: str) -> List[str]:
    formatter = string.Formatter()
    names: List[str] = []
    for _, field, _, _ in formatter.parse(tmpl):
        if field:
            if field in names:
                continue
            names.append(field)
    return names


def validate(obj: dict) -> List[str]:
    problems: List[str] = []
    if not isinstance(obj, dict):
        return ["not a mapping"]
    extra = set(obj.keys()) - _ALLOWED_KEYS
    if extra:
        problems.append(f"unknown keys: {sorted(extra)}")
    for key in ("id", "version", "template"):
        if not obj.get(key):
            problems.append(f"missing {key}")
    vars_decl = obj.get("vars", []) or []
    if not isinstance(vars_decl, list):
        problems.append("vars must be a list")
        vars_decl = []
    names = _extract_fields(obj.get("template", ""))
    declared = {v.get("name") for v in vars_decl if isinstance(v, dict)}
    for name in names:
        if name not in declared:
            problems.append(f"placeholder {name} not declared")
    for v in vars_decl:
        if not isinstance(v, dict) or "name" not in v:
            problems.append("vars entries must have name")
    return problems

