import importlib


def test_feature_flags_default_false():
    flags = importlib.reload(importlib.import_module("config.feature_flags"))
    assert not flags.EVALUATORS_ENABLED
    assert not flags.PARALLEL_EXEC_ENABLED
    assert not flags.TOT_PLANNING_ENABLED
    assert not flags.REFLECTION_ENABLED
    assert not flags.SIM_OPTIMIZER_ENABLED
    assert not flags.RAG_ENABLED


def test_run_smoke():
    from dr_rd.hrm_engine import run

    result = run("test idea")
    assert isinstance(result, dict)
    assert result
