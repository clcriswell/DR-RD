import json
import sys
import time
from pathlib import Path
from typing import Mapping


def load_config(path: str | None, lockfile: str | None, profile: str | None = None) -> Mapping:
    """Load a run configuration mapping.

    Parameters
    ----------
    path: path to a JSON config mapping.
    lockfile: path to a run_config.lock.json. If provided, ``path`` is ignored.

    Returns
    -------
    Mapping ready for adaptation to orchestrator kwargs.
    """
    if lockfile:
        from utils import run_config_io

        try:
            data = json.loads(Path(lockfile).read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - argument errors
            print(f"failed to read lockfile: {exc}", file=sys.stderr)
            sys.exit(1)
        cfg: Mapping = run_config_io.from_lockfile(data)
    elif path:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - argument errors
            print(f"failed to read config: {exc}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(data, Mapping):
            print("config JSON must be an object", file=sys.stderr)
            sys.exit(1)
        cfg = data
    else:
        cfg = {}
    if profile:
        try:
            from utils.profiles import apply_to_config
            from utils.profiles import load as load_profile

            cfg = apply_to_config(cfg, load_profile(profile))
        except Exception as exc:  # pragma: no cover - profile errors
            print(f"failed to apply profile {profile}: {exc}", file=sys.stderr)
    return cfg


def print_summary(meta: Mapping, totals: Mapping | None, *, profile: str | None = None) -> None:
    """Print a one-line summary of a run to stdout."""
    run_id = meta.get("run_id", "")
    status = meta.get("status", "")
    start = int(meta.get("started_at") or 0)
    end = int(meta.get("completed_at") or time.time())
    duration = end - start
    tokens = 0
    cost = 0.0
    if totals:
        tokens = int(totals.get("tokens") or totals.get("total_tokens") or 0)
        cost = float(totals.get("cost_usd") or totals.get("cost") or 0)
    else:
        tokens = int(meta.get("tokens") or 0)
        cost = float(meta.get("cost_usd") or 0.0)
    extra = f" {profile}" if profile else ""
    print(f"{run_id} {status} {duration} {tokens} {cost}{extra}")


def exit_code(status: str) -> int:
    """Map run status to deterministic exit codes."""
    if status == "success":
        return 0
    if status in {"cancelled", "timeout", "resumable"}:
        return 2
    return 1
