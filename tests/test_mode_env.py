from unittest.mock import MagicMock
from tests.test_app_ui import make_streamlit, reload_app


def test_env_selects_fast(monkeypatch):
    st = make_streamlit("", {}, raise_on_stop=True)
    monkeypatch.setenv("DRRD_MODE", "fast")
    reload_app(monkeypatch, st, expect_exit=True)
    assert st.session_state["MODE_CFG"]["models"]["plan"] == "gpt-4o-mini"


def test_env_invalid_warns(monkeypatch):
    st = make_streamlit("", {}, raise_on_stop=True)
    st.warning = MagicMock()
    monkeypatch.setenv("DRRD_MODE", "bogus")
    reload_app(monkeypatch, st, expect_exit=True)
    st.warning.assert_called_once_with("Unknown mode: bogus. Falling back to test.")
    assert st.session_state["MODE_CFG"]["models"]["plan"] == "gpt-3.5-turbo"
