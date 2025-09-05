from __future__ import annotations

from typing import Any, Dict, Tuple, Union

from core.redaction import Redactor


def _walk_redact(obj: Any, redactor: Redactor, mode: str):
    if isinstance(obj, str):
        r, _, _ = redactor.redact(obj, mode=mode)
        return r
    if isinstance(obj, list):
        return [_walk_redact(v, redactor, mode) for v in obj]
    if isinstance(obj, dict):
        return {k: _walk_redact(v, redactor, mode) for k, v in obj.items()}
    return obj


def pseudonymize_for_model(payload: Union[dict, str]) -> Tuple[Union[dict, str], Dict[str, str]]:
    redactor = Redactor()
    pseudo = _walk_redact(payload, redactor, "light")
    return pseudo, dict(redactor.alias_map)


def rehydrate_output(obj: Union[dict, str], alias_map: Dict[str, str]) -> Union[dict, str]:
    reverse = {v: k for k, v in alias_map.items()}

    def _walk(o: Any):
        if isinstance(o, str):
            out = o
            for alias, orig in reverse.items():
                out = out.replace(alias, orig)
            return out
        if isinstance(o, list):
            return [_walk(v) for v in o]
        if isinstance(o, dict):
            return {k: _walk(v) for k, v in o.items()}
        return o

    return _walk(obj)


def redact_for_logging(obj: Union[dict, str]) -> Union[dict, str]:
    redactor = Redactor()
    return _walk_redact(obj, redactor, "heavy")


__all__ = ["pseudonymize_for_model", "rehydrate_output", "redact_for_logging"]
