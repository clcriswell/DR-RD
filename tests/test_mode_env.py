from unittest.mock import MagicMock
from unittest.mock import MagicMock

from tests.test_app_ui import make_streamlit, reload_app


def test_env_mode_deprecated(monkeypatch):
    st = make_streamlit("", {}, raise_on_stop=True)
    st.warning = MagicMock()
    monkeypatch.setenv("DRRD_MODE", "deep")
    reload_app(monkeypatch, st, expect_exit=True)
    st.warning.assert_called_once_with("DRRD_MODE is deprecated; using standard profile.")
    assert st.session_state["MODE"] == "standard"
