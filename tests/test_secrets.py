import sys
import types

import pytest

from utils import secrets


def test_env_precedence(monkeypatch):
    monkeypatch.setenv("MY_SECRET", "123")
    assert secrets.get("MY_SECRET") == "123"


def test_streamlit_fallback(monkeypatch):
    monkeypatch.delenv("MY_SECRET", raising=False)
    fake = types.SimpleNamespace(secrets={"MY_SECRET": "abc"})
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    assert secrets.get("MY_SECRET") == "abc"


def test_require_raises(monkeypatch):
    monkeypatch.delenv("MISSING", raising=False)
    sys.modules.pop("streamlit", None)
    with pytest.raises(RuntimeError):
        secrets.require("MISSING")
