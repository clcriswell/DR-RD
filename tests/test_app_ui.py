import importlib
import os
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

    class DummySidebar:
        def checkbox(self, *args, **kwargs):
            return False
        def expander(self, *args, **kwargs):
            class DummyExpander:
                def __enter__(self_inner):
                    return None
                def __exit__(self_inner, exc_type, exc, tb):
                    return False
            return DummyExpander()

    class DummyForm:
        def __enter__(self):
            return None
        def __exit__(self, exc_type, exc, tb):
            return False

    # Added selectbox to dummy streamlit with default "Medium"
    st = SimpleNamespace(
        session_state=state,
        secrets={"gcp_service_account": {}},
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
        slider=MagicMock(return_value=1),
        checkbox=MagicMock(return_value=False),
        selectbox=MagicMock(return_value="Medium"),  # Design Depth default
        form=lambda key: DummyForm(),
        form_submit_button=MagicMock(return_value=True),
        write=MagicMock(),
        sidebar=DummySidebar(),
        image=MagicMock(),
        caption=MagicMock(),
    )
    return st


def reload_app(monkeypatch, st, patches=None, expect_exit=False):
    monkeypatch.setitem(sys.modules, "streamlit", st)
    # Patch Google Cloud logging to avoid needing real credentials
    monkeypatch.setattr(
        "google.oauth2.service_account.Credentials.from_service_account_info",
        lambda info: None,
    )
    class DummyClient:
        def __init__(self, credentials=None):
            pass
        def setup_logging(self):
            pass
    monkeypatch.setattr("google.cloud.logging.Client", lambda credentials=None: DummyClient())
    if patches:
        for target, ret in patches.items():
            monkeypatch.setattr(target, ret)
    for mod in list(sys.modules):
        if mod.startswith("app"):
            del sys.modules[mod]
    module = importlib.import_module("app")
    if expect_exit:
        with pytest.raises(SystemExit):
            module.main()
    else:
        module.main()


def test_empty_idea_shows_info(monkeypatch):
    st = make_streamlit("", {}, raise_on_stop=True)
    reload_app(monkeypatch, st, expect_exit=True)
    assert st.info.call_args[0][0] == "Please describe an idea to get started."


def test_generate_plan_updates_state(monkeypatch):
    st = make_streamlit(
        "idea",
        {"1⃣ Generate Research Plan": True},
    )
    patches = {
        "agents.planner_agent.PlannerAgent.run": (
            lambda self, idea, task, difficulty="normal": [
                {"role": "CTO", "title": "t1", "description": "d1"},
                {"role": "X", "title": "t2", "description": "d2"},
            ]
        )
    }
    reload_app(monkeypatch, st, patches)
    plan = st.session_state["plan"]
    assert any(t == {"role": "CTO", "title": "t1", "description": "d1"} for t in plan)
    assert all(t.get("role") != "X" for t in plan)
    st.warning.assert_not_called()


def test_run_domain_experts(monkeypatch):
    state = {
        "plan": [
            {"role": "CTO", "title": "task", "description": "desc"},
            {"role": "Finance", "title": "budget", "description": "plan"},
        ]
    }
    st = make_streamlit(
        "idea",
        {"2⃣ Run All Domain Experts": True},
        state=state,
    )
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    patches = {
        "agents.base_agent.BaseAgent.run": lambda self, idea, task, design_depth="Medium": "out",
        "dr_rd.utils.llm_client.llm_call": lambda *a, **k: type(
            "R",
            (),
            {
                "choices": [
                    type("C", (), {"message": type("M", (), {"content": "out"})()})
                ]
            },
        )(),
        "agents.synthesizer.llm_call": lambda *a, **k: type(
            "R",
            (),
            {
                "choices": [
                    type("C", (), {"message": type("M", (), {"content": "out"})()})
                ]
            },
        )(),
    }
    reload_app(monkeypatch, st, patches)
    assert st.session_state["answers"] == {"CTO": "out", "Finance": "out"}


def test_compile_final_proposal(monkeypatch):
    state = {"answers": {"Mechanical Systems Lead": "out"}, "plan": []}
    st = make_streamlit(
        "idea",
        {"3⃣ Compile Final Proposal": True},
        state=state,
    )
    patches = {
        "agents.synthesizer.compose_final_proposal": (
            lambda idea, answers, include_simulations=False: {"document": "final", "images": []}
        )
    }
    reload_app(monkeypatch, st, patches)
    st.markdown.assert_called_with("final")

