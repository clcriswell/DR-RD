from core import router


class EchoAgent:
    def run(self, *, task=None, model=None, meta=None):
        return {"task": task, "model": model}


def test_router_success(monkeypatch):
    monkeypatch.setattr(router, "AGENT_REGISTRY", {"Echo": object, "Synthesizer": object})
    monkeypatch.setattr(router, "get_agent", lambda name: EchoAgent())
    monkeypatch.setattr(
        router,
        "select_model",
        lambda purpose, ui_model, agent_name=None: ui_model or "m",
    )

    task = {"role": "Echo", "title": "hi"}
    result = router.dispatch(task, ui_model="model-x")
    assert result["task"] is task
    assert result["model"] == "model-x"
