# core/privacy.py
from typing import Any, Dict, Iterable, Tuple, Optional
from core.redaction import Redactor

_MODEL_REDACTOR = Redactor()
_LOG_REDACTOR = Redactor()


def set_project_terms(terms: Iterable[str], category: str = "PERSON", role: Optional[str] = None) -> None:
    _MODEL_REDACTOR.add_allowed_entities(terms, category=category, role=role)
    _LOG_REDACTOR.add_allowed_entities(terms, category=category, role=role)


def _reset(r: Redactor) -> None:
    r.alias_map.clear()
    for k in r.counters:
        r.counters[k] = 0


def pseudonymize_for_model(payload: Any, role: Optional[str] = None) -> Tuple[Any, Dict[str, str]]:
    r = _MODEL_REDACTOR
    _reset(r)

    def walk(x):
        if isinstance(x, str):
            red, _, _ = r.redact(x, mode="light", role=role)
            return red
        if isinstance(x, list):
            return [walk(i) for i in x]
        if isinstance(x, dict):
            return {k: walk(v) for k, v in x.items()}
        return x

    return walk(payload), dict(r.alias_map)

def redact_for_logging(obj: Any) -> Any:
    r = _LOG_REDACTOR
    _reset(r)

    def walk(x):
        if isinstance(x, str):
            red, _, _ = r.redact(x, mode="logging", role=None)
            return red
        if isinstance(x, list):
            return [walk(i) for i in x]
        if isinstance(x, dict):
            return {k: walk(v) for k, v in x.items()}
        return x

    return walk(obj)

def rehydrate_output(obj: Any, alias_map: Dict[str,str]) -> Any:
    rev = {v: k for k, v in alias_map.items()}

    def walk(x):
        if isinstance(x, str):
            for a, real in rev.items():
                x = x.replace(a, real)
            return x
        if isinstance(x, list):
            return [walk(i) for i in x]
        if isinstance(x, dict):
            return {k: walk(v) for k, v in x.items()}
        return x

    return walk(obj)
