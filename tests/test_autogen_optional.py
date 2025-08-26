import pytest

from config import feature_flags as ff


def test_autogen_optional():
    if not ff.AUTOGEN_ENABLED:
        pytest.skip("autogen disabled")
    autogen = pytest.importorskip("autogen")
    from core.autogen.run import run_autogen

    text, answers, trace = run_autogen("hi")
    assert "autogen_trace" in trace and isinstance(trace["autogen_trace"], list)
