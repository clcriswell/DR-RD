import pytest

from dataclasses import FrozenInstanceError

import streamlit as st

from dr_rd.prompting import (
    PromptRegistry,
    PromptTemplate,
    RetrievalPolicy,
    registry,
)
from core import orchestrator


def test_register_get_list():
    registry = PromptRegistry()
    tpl = PromptTemplate(
        id="demo",
        version="v1",
        role="Demo",
        task_key=None,
        system="sys",
        user_template="user",
        io_schema_ref="schema.json",
        retrieval_policy=RetrievalPolicy.NONE,
    )
    registry.register(tpl)
    assert registry.get("Demo") == tpl
    assert registry.list("Demo") == [tpl]
    assert registry.list() == [tpl]


def test_version_overwrite():
    registry = PromptRegistry()
    tpl1 = PromptTemplate(
        id="demo",
        version="v1",
        role="Demo",
        task_key=None,
        system="s1",
        user_template="u1",
        io_schema_ref="schema.json",
        retrieval_policy=RetrievalPolicy.NONE,
    )
    tpl2 = PromptTemplate(
        id="demo",
        version="v2",
        role="Demo",
        task_key=None,
        system="s2",
        user_template="u2",
        io_schema_ref="schema.json",
        retrieval_policy=RetrievalPolicy.NONE,
    )
    registry.register(tpl1)
    registry.register(tpl2)
    retrieved = registry.get("Demo")
    assert retrieved.version == "v2"
    assert retrieved.system == "s2"


def test_planner_registered():
    tpl = registry.get("Planner")
    assert tpl is not None
    assert "Planner" in tpl.system
    assert tpl.io_schema_ref.endswith("planner_v1.json")


def test_templates_immutable():
    tpl = registry.get("Planner")
    try:
        tpl.system = "hack"  # type: ignore[attr-defined]
    except FrozenInstanceError:
        pass
    else:  # pragma: no cover - should not happen
        assert False, "PromptTemplate should be immutable"


def test_generate_plan_uses_registry(monkeypatch):
    captured: dict = {}

    def fake_complete(system, user, **kwargs):
        captured["system"] = system
        class R:
            content = (
                '{"tasks":[{"id":"T01","title":"t","summary":"s","description":"d","role":"CTO"}]}'
            )

        return R()

    monkeypatch.setattr(orchestrator, "complete", fake_complete)
    st.session_state["prompt_texts"] = {"planner": "OVERRIDE"}
    orchestrator.generate_plan("idea")
    assert captured["system"] == registry.get("Planner").system
