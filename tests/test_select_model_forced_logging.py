import logging

from core.llm import select_model


def test_select_model_forced_logging(monkeypatch, caplog):
    monkeypatch.setenv("DRRD_MODEL_AGENT_SYNTHESIZER", "gpt-4-turbo")
    monkeypatch.setenv("DRRD_FORCE_MODEL", "gpt-4.1-mini")
    caplog.set_level(logging.WARNING)
    model = select_model("agent", None, agent_name="Synthesizer")
    assert model == "gpt-4.1-mini"
    msg = caplog.records[0].message
    assert (
        "FORCING model override: gpt-4-turbo -> gpt-4.1-mini" in msg
        and "agent=Synthesizer" in msg
    )
