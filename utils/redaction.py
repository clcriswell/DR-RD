# utils/redaction.py
from core.redaction import Redactor, redact_text


def redact_public(text: str) -> str:
    """Redact ``text`` for public logs using heavy mode."""
    return Redactor().redact(text, mode="heavy")[0]

def redact_dict(obj, mode: str = "heavy"):
    r = Redactor()
    def walk(x):
        if isinstance(x, str):
            red, _, _ = r.redact(x, mode=mode, role=None)
            return red
        if isinstance(x, list):
            return [walk(i) for i in x]
        if isinstance(x, dict):
            return {k: walk(v) for k,v in x.items()}
        return x
    return walk(obj)

def load_policy(_):  # back-compat no-op
    return {}
