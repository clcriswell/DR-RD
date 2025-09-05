# core/privacy.py
from typing import Any, Dict, Tuple
from core.redaction import Redactor

def pseudonymize_for_model(payload: Any) -> Tuple[Any, Dict[str,str]]:
    r = Redactor()
    def walk(x):
        if isinstance(x, str):
            red, _, _ = r.redact(x, mode="light", role=None)
            return red
        if isinstance(x, list):
            return [walk(i) for i in x]
        if isinstance(x, dict):
            return {k: walk(v) for k,v in x.items()}
        return x
    return walk(payload), dict(r.alias_map)

def redact_for_logging(obj: Any) -> Any:
    r = Redactor()
    def walk(x):
        if isinstance(x, str):
            red, _, _ = r.redact(x, mode="heavy", role=None)
            return red
        if isinstance(x, list):
            return [walk(i) for i in x]
        if isinstance(x, dict):
            return {k: walk(v) for k,v in x.items()}
        return x
    return walk(obj)

def rehydrate_output(obj: Any, alias_map: Dict[str,str]) -> Any:
    # no-op placeholder: reverse-map if needed in future
    return obj
