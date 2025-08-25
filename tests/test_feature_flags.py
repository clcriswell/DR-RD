import importlib


def test_feature_flags_default_false(monkeypatch):
    for name in [
        "EVALUATORS_ENABLED",
        "PARALLEL_EXEC_ENABLED",
        "TOT_PLANNING_ENABLED",
        "REFLECTION_ENABLED",
        "SIM_OPTIMIZER_ENABLED",
        "RAG_ENABLED",
    ]:
        monkeypatch.delenv(name, raising=False)

    flags = importlib.reload(importlib.import_module("config.feature_flags"))

    assert not flags.EVALUATORS_ENABLED
    assert not flags.PARALLEL_EXEC_ENABLED
    assert not flags.TOT_PLANNING_ENABLED
    assert not flags.REFLECTION_ENABLED
    assert not flags.SIM_OPTIMIZER_ENABLED
    assert not flags.RAG_ENABLED


def test_apply_overrides(monkeypatch):
    import config.feature_flags as ff

    ff.RAG_ENABLED = False
    ff.ENABLE_LIVE_SEARCH = True
    ff.apply_overrides({"rag_enabled": True, "live_search_enabled": False})
    assert ff.RAG_ENABLED is True
    assert ff.ENABLE_LIVE_SEARCH is False
