from __future__ import annotations

import json
import os
from typing import Optional

from dotenv import load_dotenv
import streamlit as st

load_dotenv()

def _from_secrets(key: str) -> Optional[str]:
    try:
        for k, v in st.secrets.items():
            if k.lower() == key.lower():
                return v if isinstance(v, str) else json.dumps(v)
    except Exception:
        return None
    return None

def get_env(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key)
    if value is not None:
        return value
    secret_val = _from_secrets(key)
    if secret_val is not None:
        return secret_val
    return default

def require_env(key: str) -> str:
    value = get_env(key)
    if value is None or value == "":
        message = f"Missing required environment variable: {key}"
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx

            if get_script_run_ctx() is not None:
                st.error(message)
                st.stop()
        except Exception:
            pass
        raise RuntimeError(message)
    return value

__all__ = ["get_env", "require_env"]
