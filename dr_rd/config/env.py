from __future__ import annotations

import json
import os
from collections.abc import Mapping

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _from_secrets(key: str) -> str | None:
    try:
        for k, v in st.secrets.items():
            if k.lower() == key.lower():
                if isinstance(v, str):
                    return v
                if isinstance(v, Mapping):
                    return json.dumps(dict(v))
                return json.dumps(v)
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
