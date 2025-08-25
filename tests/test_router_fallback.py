import logging

from core import router


class NoCall:
    pass


class RS:
    def run(self, *, task=None, model=None, meta=None):
        return "rs"


def test_router_fallback(monkeypatch, caplog):
    monkeypatch.setattr(router, "AGENT_REGISTRY", {"Bad": object, "Research Scientist": object})

    def fake_get_agent(name):
        return NoCall() if name == "Bad" else RS()

    monkeypatch.setattr(router, "get_agent", fake_get_agent)
    monkeypatch.setattr(
        router, "select_model", lambda purpose, ui_model, agent_name=None: "m"
    )

    task = {"role": "Bad", "title": "x"}
    with caplog.at_level(logging.WARNING):
        result = router.dispatch(task)
    assert result == "rs"
    warnings = [r for r in caplog.records if r.levelname == "WARNING"]
    assert len(warnings) == 1
    assert "Bad" in warnings[0].message
