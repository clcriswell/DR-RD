import importlib
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def make_streamlit(text_input, buttons, state=None, raise_on_stop=False):
    if state is None:
        state = {}

    def button(label):
        return buttons.get(label, False)

    class DummySpinner:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    st = SimpleNamespace(
        session_state=state,
        set_page_config=lambda *a, **k: None,
        title=lambda *a, **k: None,
        text_input=lambda *a, **k: text_input,
        info=MagicMock(),
        stop=MagicMock(side_effect=SystemExit if raise_on_stop else None),
        button=button,
        spinner=lambda msg: DummySpinner(),
        subheader=MagicMock(),
        json=MagicMock(),
        markdown=MagicMock(),
        warning=MagicMock(),
    )
    return st


def reload_app(monkeypatch, st, patches=None, expect_exit=False):
    monkeypatch.setitem(sys.modules, "streamlit", st)
    if patches:
        for target, ret in patches.items():
            monkeypatch.setattr(target, ret)
    if "app" in sys.modules:
        del sys.modules["app"]
    if expect_exit:
        with pytest.raises(SystemExit):
            importlib.import_module("app")
    else:
        importlib.import_module("app")


def test_empty_idea_shows_info(monkeypatch):
    st = make_streamlit("", {}, raise_on_stop=True)
    reload_app(monkeypatch, st, expect_exit=True)
    assert st.info.call_args[0][0] == "Please describe an idea to get started."


def test_generate_plan_updates_state(monkeypatch):
    st = make_streamlit(
        "idea",
        {"1\u20e3 Generate Research Plan": True},
    )
    patches = {
        "agents.planner_agent.PlannerAgent.run": lambda self, idea, task: {"X": "Y"}
    }
    reload_app(monkeypatch, st, patches)
    assert st.session_state["plan"] == {"X": "Y"}


def test_run_domain_experts(monkeypatch):
    state = {"plan": {"CTO": "task", "Engineer": "task"}}
    st = make_streamlit(
        "idea",
        {"2\u20e3 Run All Domain Experts": True},
        state=state,
    )
    patches = {
        "agents.base_agent.BaseAgent.run": lambda self, idea, task: "out"
    }
    reload_app(monkeypatch, st, patches)
    assert st.session_state["answers"] == {"CTO": "out", "Engineer": "out"}


def test_compile_final_proposal(monkeypatch):
    state = {"answers": {"CTO": "out"}}
    st = make_streamlit(
        "idea",
        {"3\u20e3 Compile Final Proposal": True},
        state=state,
    )
    patches = {
        "agents.synthesizer.compose_final_proposal": lambda idea, answers: "final"
    }
    reload_app(monkeypatch, st, patches)
    st.markdown.assert_called_with("final")
