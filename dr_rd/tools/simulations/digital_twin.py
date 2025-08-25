"""Lightweight digital twin simulator."""
from __future__ import annotations

import random
from typing import Dict, Any, List


def _run_model(inputs: Dict[str, Any], rng: random.Random | None = None) -> Dict[str, float]:
    base = sum(v for v in inputs.values() if isinstance(v, (int, float)))
    noise = rng.uniform(-0.5, 0.5) if rng else 0.0
    return {"output": base + noise}


def simulate(params: Dict[str, Any]) -> Dict[str, Any]:
    """Run the digital twin model.

    Supports:
    - single run: {"x": 1}
    - parameter sweeps: {"sweep": [{...}, {...}]}
    - monte carlo: {"monte_carlo": int, ...}
    Optional key "seed" ensures deterministic runs.
    """
    rng = random.Random(params.get("seed"))

    if "sweep" in params:
        runs = [_run_model(p, rng) for p in params["sweep"]]
        return {"runs": runs}

    if "monte_carlo" in params:
        n = int(params["monte_carlo"])
        runs = [_run_model(params, rng) for _ in range(n)]
        mean = sum(r["output"] for r in runs) / n if n else 0.0
        return {"runs": runs, "mean_output": mean}

    return _run_model(params, rng)
