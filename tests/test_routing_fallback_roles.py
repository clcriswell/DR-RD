import streamlit as st

from core.router import route_task
from core.agents.unified_registry import AGENT_REGISTRY


def test_unknown_role_falls_back(tmp_path, monkeypatch):
    st.session_state.clear()
    task = {"id": "1", "title": "t", "description": "d", "role": "Unknown"}
    role, *_ = route_task(task)
    assert role == "Dynamic Specialist"
    task2 = {"id": "2", "title": "t", "description": "d"}
    role2, *_ = route_task(task2)
    assert role2 == "Dynamic Specialist"


def test_qa_synonyms(monkeypatch):
    task = {"id": "3", "title": "t", "description": "d", "role": "qa"}
    role, *_ = route_task(task)
    assert role == "QA"
    task2 = {"id": "4", "title": "t", "description": "d", "role": "quality assurance"}
    role2, *_ = route_task(task2)
    assert role2 == "QA"
    monkeypatch.delitem(AGENT_REGISTRY, "QA", raising=False)
    role3, *_ = route_task(task)
    assert role3 == "Dynamic Specialist"
