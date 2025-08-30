from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from utils.telemetry import flag_checked

FLAGS_PATH = Path('.dr_rd/flags.json')


def _ensure_file() -> None:
    if FLAGS_PATH.exists():
        return
    FLAGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    default = {"version": 1, "flags": {}}
    FLAGS_PATH.write_text(json.dumps(default, indent=2), encoding='utf-8')


def load_flags() -> Dict[str, Any]:
    _ensure_file()
    try:
        return json.loads(FLAGS_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {"version": 1, "flags": {}}


def is_enabled(name: str, *, params: dict[str, str] | None = None) -> bool:
    params = params or {}
    key = f'f_{name}'
    raw = params.get(key)
    value: bool | None = None
    if raw is not None:
        if raw.lower() in {'1', 'true'}:
            value = True
        elif raw.lower() in {'0', 'false'}:
            value = False
    if value is None:
        env = os.getenv(f'FLAG_{name.upper()}')
        if env is not None:
            if env.lower() in {'1', 'true'}:
                value = True
            elif env.lower() in {'0', 'false'}:
                value = False
    if value is None:
        flags = load_flags().get('flags', {})
        value = bool(flags.get(name, False))
    flag_checked(name, value)
    return value


def all_flags() -> Dict[str, bool]:
    flags = load_flags().get('flags', {})
    return {k: bool(v) for k, v in flags.items()}

