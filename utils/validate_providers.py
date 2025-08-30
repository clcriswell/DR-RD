from __future__ import annotations

import os
import time
from typing import Dict

from .secrets import get as secret_get


def quick_probe(provider: str, model: str, timeout_sec: float = 2.0) -> Dict:
    """Light connectivity/credentials check for provider/model."""
    if os.getenv("NO_NET") == "1":
        return {"status": "skip"}
    start = time.time()
    try:
        if provider == "openai":
            try:
                from openai import OpenAI
            except Exception:
                return {"status": "warn"}
            key = secret_get("OPENAI_API_KEY")
            if not key:
                return {"status": "fail"}
            client = OpenAI(api_key=key, timeout=timeout_sec)
            client.models.retrieve(model)
            return {"status": "pass"}
        if provider == "anthropic":
            try:
                import anthropic
            except Exception:
                return {"status": "warn"}
            key = secret_get("ANTHROPIC_API_KEY")
            if not key:
                return {"status": "fail"}
            client = anthropic.Anthropic(api_key=key, timeout=timeout_sec)
            client.models.retrieve(model)
            return {"status": "pass"}
    except Exception:
        return {"status": "fail"}
    finally:
        _ = time.time() - start
    return {"status": "warn"}

