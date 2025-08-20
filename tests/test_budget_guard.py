from unittest.mock import MagicMock
from tests.test_app_ui import make_streamlit, reload_app
import core.llm_client as lc


def test_budget_guard(monkeypatch):
    st = make_streamlit("", {}, raise_on_stop=True)
    st.error = MagicMock()
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setattr(lc, "set_budget_manager", lambda _: None)
    monkeypatch.setattr(lc, "BUDGET", None, raising=False)
    reload_app(monkeypatch, st, expect_exit=True)
    st.error.assert_called_once_with("Budget manager not installed. Fix config before running.")
