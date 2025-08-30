"""Capture a snapshot of the current Python environment."""

from __future__ import annotations

import platform
import sys
import time


def capture_env() -> dict[str, object]:
    """Return a JSON-serializable snapshot of the runtime environment."""
    info: dict[str, object] = {
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "created_at": int(time.time()),
        "packages": {},
    }
    try:
        import pkg_resources  # type: ignore

        info["packages"] = {d.project_name: d.version for d in pkg_resources.working_set}
    except Exception:
        try:
            import importlib.metadata as md  # type: ignore

            info["packages"] = {
                dist.metadata.get("Name", dist.name): dist.version for dist in md.distributions()
            }
        except Exception:
            info["packages"] = {}
    return info
