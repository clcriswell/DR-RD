from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Tuple

EXP_PATH = Path(".dr_rd/experiments.json")


def _load_registry() -> dict:
    try:
        return json.loads(EXP_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "experiments": {}}


def hash_bucket(user_id: str, exp_id: str, salt: str, weights: list[float]) -> int:
    h = hashlib.sha256((user_id + exp_id + salt).encode("utf-8")).hexdigest()
    v = int(h, 16) / 2 ** 256
    acc = 0.0
    for i, w in enumerate(weights):
        acc += w
        if v < acc:
            return i
    return len(weights) - 1


def assign(user_id: str, exp_id: str) -> Tuple[str, int]:
    reg = _load_registry().get("experiments", {})
    cfg = reg.get(exp_id)
    if not cfg:
        return ("control", 0)
    idx = hash_bucket(user_id, exp_id, cfg.get("salt", ""), cfg.get("weights", []))
    variants = cfg.get("variants", [])
    name = variants[idx] if idx < len(variants) else "control"
    return name, idx


def force_from_params(params: dict[str, str], exp_id: str) -> str | None:
    key = f"exp_{exp_id}"
    return params.get(key)


def _hash(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:16]


def exposure(evlog, user_id: str, exp_id: str, variant: str, *, run_id: str | None = None):
    ev = {
        "event": "exp_exposed",
        "user_id": _hash(user_id),
        "exp_id": exp_id,
        "variant": variant,
    }
    if run_id:
        ev["run_id"] = run_id
    evlog(ev)
