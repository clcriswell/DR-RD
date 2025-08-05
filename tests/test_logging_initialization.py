import importlib
import sys
from types import SimpleNamespace


def make_st(secrets):
    return SimpleNamespace(session_state={}, secrets=secrets)


def reload_app_with_streamlit(monkeypatch, st):
    monkeypatch.setitem(sys.modules, "streamlit", st)
    for mod in list(sys.modules):
        if mod.startswith("app"):
            del sys.modules[mod]
    return importlib.import_module("app")


def test_skips_logging_without_secrets(monkeypatch):
    st = make_st({})
    app = reload_app_with_streamlit(monkeypatch, st)
    called = False

    def fake_init():
        nonlocal called
        called = True
        return True

    monkeypatch.setattr(app, "init_gcp_logging", fake_init)
    app.maybe_init_gcp_logging()
    assert called is False
    assert st.session_state["gcp_logging_initialized"] is False


def test_memoizes_logging(monkeypatch):
    st = make_st({"gcp_service_account": {"private_key": "x"}})
    app = reload_app_with_streamlit(monkeypatch, st)
    calls = 0

    def fake_init():
        nonlocal calls
        calls += 1
        return True

    monkeypatch.setattr(app, "init_gcp_logging", fake_init)
    app.maybe_init_gcp_logging()
    app.maybe_init_gcp_logging()
    assert calls == 1
    assert st.session_state["gcp_logging_initialized"] is True
