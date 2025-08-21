import types
import os
import core.llm_client as llm_client
from core import router


def _run(task, ui_model, monkeypatch):
    captured = {}

    def fake_call(model, messages, **kwargs):
        captured["model"] = model
        return {"raw": types.SimpleNamespace(), "text": ""}

    monkeypatch.setattr(llm_client, "call_openai", fake_call)
    monkeypatch.setattr("core.llm.call_openai", fake_call)
    role, cls, model, routed = router.route_task(task, ui_model)
    agent = cls(model)
    try:
        agent.act("idea", routed, model=model)
    except Exception:
        try:
            agent.run("idea", {}, model=model)
        except Exception:
            pass
    return captured.get("model")


def test_ui_model(monkeypatch):
    task = {"role": "Research Scientist", "title": "t", "description": "d"}
    used = _run(task, "ui-model", monkeypatch)
    assert used == "ui-model"


def test_env_model(monkeypatch):
    task = {"role": "Research Scientist", "title": "t", "description": "d"}
    monkeypatch.delenv("DRRD_FORCE_MODEL", raising=False)
    monkeypatch.setenv("DRRD_MODEL_AGENT", "env-model")
    used = _run(task, None, monkeypatch)
    assert used == "env-model"
    monkeypatch.delenv("DRRD_MODEL_AGENT", raising=False)


def test_per_agent_override(monkeypatch):
    monkeypatch.delenv("DRRD_MODEL_AGENT", raising=False)
    monkeypatch.setenv("DRRD_MODEL_AGENT_SYNTHESIZER", "synth-model")
    synth_task = {"role": "Synthesizer", "title": "", "description": ""}
    used_s = _run(synth_task, None, monkeypatch)
    assert used_s == "synth-model"
    rs_task = {"role": "Research Scientist", "title": "t", "description": "d"}
    used_r = _run(rs_task, None, monkeypatch)
    assert used_r == "gpt-4.1-mini"
    monkeypatch.delenv("DRRD_MODEL_AGENT_SYNTHESIZER", raising=False)


def test_force_model(monkeypatch):
    task = {"role": "Research Scientist", "title": "t", "description": "d"}
    monkeypatch.setenv("DRRD_FORCE_MODEL", "forced")
    used = _run(task, "ui-model", monkeypatch)
    assert used == "forced"
    monkeypatch.delenv("DRRD_FORCE_MODEL", raising=False)
