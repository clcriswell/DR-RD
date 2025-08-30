"""Helpers for reproducing previous runs."""

from __future__ import annotations

import json
from typing import Any, Mapping

from . import run_config_io
from .paths import artifact_path
from .run_config import RunConfig
from .run_config import to_orchestrator_kwargs as _to_orch_kwargs


def load_run_inputs(run_id: str) -> dict[str, Any]:
    """Read run_config.lock.json; raise FileNotFoundError if missing."""
    path = artifact_path(run_id, "run_config", "lock.json")
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def to_orchestrator_kwargs(locked: Mapping[str, Any]) -> dict[str, Any]:
    """Map lockfile 'inputs' → orchestrator kwargs (single place)."""
    cfg_dict = run_config_io.from_lockfile(locked)
    seed = cfg_dict.pop("seed", None)
    cfg_dict.pop("prompts", None)
    rc = RunConfig(**cfg_dict)
    kwargs = _to_orch_kwargs(rc)
    if seed is not None:
        kwargs["seed"] = seed
    return kwargs


def diff_configs(a: Mapping[str, Any], b: Mapping[str, Any]) -> dict[str, Any]:
    """Return entries in ``b`` that differ from ``a`` (shallow)."""
    out: dict[str, Any] = {}
    for k, v in b.items():
        if a.get(k) != v:
            out[k] = v
    return out
