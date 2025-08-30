import streamlit as st

from app.ui.a11y import inject_accessibility_baseline


def test_inject_accessibility_baseline(monkeypatch):
    captured = {}

    def fake_markdown(content, unsafe_allow_html=False):
        captured["content"] = content
        captured["unsafe"] = unsafe_allow_html

    monkeypatch.setattr(st, "markdown", fake_markdown)
    inject_accessibility_baseline()

    assert captured["unsafe"] is True
    assert ":root { --focus-ring" in captured["content"]

