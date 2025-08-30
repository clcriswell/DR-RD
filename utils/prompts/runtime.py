"""Runtime prompt rendering and pinning."""
from __future__ import annotations

from typing import Mapping, Tuple

from .loader import load, hash_prompt


def _escape(v: str) -> str:
    return v.replace("{", "{{").replace("}", "}}")


def render(id_: str, values: Mapping[str, str] | None = None) -> Tuple[str, dict]:
    obj = load(id_)
    values = dict(values or {})
    rendered_vars = {}
    for var in obj.get("vars", []) or []:
        name = var.get("name")
        default = var.get("default")
        required = bool(var.get("required"))
        if name in values:
            rendered_vars[name] = _escape(str(values[name]))
        elif not required:
            if default is not None:
                rendered_vars[name] = _escape(str(default))
        else:
            raise KeyError(f"missing required var {name}")
    text = obj["template"].format(**rendered_vars)
    pin = {"id": obj["id"], "version": obj["version"], "hash": hash_prompt(obj)}
    return text, pin

_ROLE_ALIASES = {
    "planner": "planner",
    "executor": "executor",
    "synthesizer": "synthesizer",
}


def get_prompt_text(role: str, cfg) -> Tuple[str, dict]:
    id_ = _ROLE_ALIASES.get(role, role)
    values = {}
    if cfg and getattr(cfg, "knowledge_hint", None):
        values["knowledge_hint"] = getattr(cfg, "knowledge_hint")
    if cfg and getattr(cfg, "tone", None):
        values["tone"] = getattr(cfg, "tone")
    return render(id_, values)

