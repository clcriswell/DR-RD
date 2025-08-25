from types import SimpleNamespace

from core.agents import synthesizer_agent as sa
from core.agents.synthesizer_agent import compose_final_proposal


def test_images_disabled(monkeypatch):
    class DummySt:
        session_state = {"final_flags": {"ENABLE_IMAGES": False}}

    monkeypatch.setattr(sa, "st", DummySt)

    called = {"make": False}

    def fake_make(*args, **kwargs):  # pragma: no cover - invoked only on failure
        called["make"] = True
        return []

    monkeypatch.setattr(sa, "make_visuals_for_project", fake_make)
    monkeypatch.setattr(
        sa,
        "complete",
        lambda *a, **k: SimpleNamespace(content="doc", raw={"usage": SimpleNamespace(prompt_tokens=0, completion_tokens=0)}),
    )

    out = compose_final_proposal("idea", {"Role": "Answer"})
    assert out["images"] == []
    assert called["make"] is False
