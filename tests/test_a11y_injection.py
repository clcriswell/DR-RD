import importlib.util
from pathlib import Path

import streamlit as st

spec = importlib.util.spec_from_file_location("a11y", Path("app/ui/a11y.py"))
a11y = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a11y)


def test_inject(monkeypatch):
    calls = []

    def fake_markdown(content, unsafe_allow_html=False):
        calls.append(content)

    monkeypatch.setattr(st, "markdown", fake_markdown)
    st.session_state.clear()
    a11y.inject()
    assert any("skip-link" in c for c in calls)
