import json
from unittest.mock import Mock, patch

import core.orchestrator as orchestrator
from core.orchestrator import _invoke_agent, compose_final_proposal, execute_plan, generate_plan


@patch("core.orchestrator.complete")
def test_generate_plan_parses_llm_output(mock_complete):
    mock_complete.return_value = Mock(
        content='{"tasks": [{"role": "CTO", "title": "Plan", "summary": "Design"}]}'
    )
    tasks = generate_plan("new idea")
    assert tasks == [
        {
            "id": "T01",
            "role": "CTO",
            "title": "Plan",
            "description": "Design",
            "summary": "Design",
        }
    ]
    mock_complete.assert_called_once()


@patch("core.orchestrator.route_task")
def test_execute_plan_routes_and_invokes_agents(mock_route, monkeypatch):
    monkeypatch.setattr("core.evaluation.self_check._load_schema", lambda role: None)

    class DummyAgent:
        def __init__(self, model):
            self.model = model

    mock_route.side_effect = [
        (
            "Research Scientist",
            DummyAgent,
            "m1",
            {"title": "t1", "description": "d1", "role": "Research Scientist", "stop_rules": []},
        ),
        (
            "Research Scientist",
            DummyAgent,
            "m1",
            {"title": "t2", "description": "d2", "role": "Research Scientist", "stop_rules": []},
        ),
    ]

    def side_effect(agent, task, model=None, meta=None, run_id=None):
        return json.dumps(
            {
                "role": "Research Scientist",
                "task": task.get("title"),
                "findings": ["f"],
                "risks": ["r"],
                "next_steps": ["n"],
                "sources": [],
            }
        )

    monkeypatch.setattr(orchestrator, "invoke_agent_safely", side_effect)
    tasks = [
        {"role": "Research Scientist", "title": "t1", "description": "d1"},
        {"role": "Research Scientist", "title": "t2", "description": "d2"},
    ]
    answers = execute_plan("idea", tasks, agents={}, ui_model=None)
    outs = answers["Research Scientist"].split("\n\n")
    assert len(outs) == 2
    assert all(json.loads(o)["task"] in {"t1", "t2"} for o in outs)
    assert mock_route.call_count == 2


def test_invoke_agent_handles_string_task():
    class DummyAgent:
        def run(self, context, task, model=None):
            assert isinstance(task, dict)
            return f"{task.get('title')}-{task.get('description')}"

    out = _invoke_agent(DummyAgent(), "ctx", "simple task")
    assert out == "simple task-simple task"


@patch("core.orchestrator.complete")
def test_compose_final_proposal_formats_findings(mock_complete, monkeypatch):
    mock_complete.return_value = Mock(content=" final plan ")
    answers = {"CTO": "analysis"}
    monkeypatch.setattr(orchestrator, "pseudonymize_for_model", lambda x: (x, {}))
    import streamlit as st

    st.session_state.clear()
    result = compose_final_proposal("idea", answers)
    assert result == "final plan"
    system_prompt, prompt = mock_complete.call_args[0]
    assert "analysis" in prompt and "idea" in prompt


@patch("core.orchestrator.complete")
def test_open_issues_in_prompt(mock_complete, monkeypatch):
    mock_complete.return_value = Mock(content="done")
    import streamlit as st

    st.session_state.clear()
    st.session_state["answers_raw"] = {
        "Research": [
            json.dumps(
                {
                    "findings": "Not determined",
                    "risks": "Not determined",
                    "next_steps": "Not determined",
                }
            )
        ]
    }
    st.session_state["open_issues"] = [{"title": "t", "role": "Research"}]
    st.session_state["alias_maps"] = {}
    monkeypatch.setattr(orchestrator, "pseudonymize_for_model", lambda x: (x, {}))
    compose_final_proposal("idea", {})
    _, prompt = mock_complete.call_args[0]
    assert "### Research" in prompt
    assert "[No data provided]" in prompt
    assert "Open Issues" not in prompt


@patch("core.orchestrator.complete")
def test_final_report_fallback(mock_complete):
    mock_complete.return_value = Mock(content="")
    import streamlit as st

    st.session_state.clear()
    st.session_state["answers_raw"] = {
        "Research": [
            json.dumps(
                {
                    "findings": "Not determined",
                    "risks": "Not determined",
                    "next_steps": "Not determined",
                }
            )
        ]
    }
    st.session_state["open_issues"] = [{"title": "t", "role": "Research"}]
    st.session_state["alias_maps"] = {}
    out = compose_final_proposal("idea", {})
    assert out.strip() != ""
    assert "## Gaps and Unresolved Issues" in out
