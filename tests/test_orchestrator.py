from unittest.mock import Mock, patch

from core.orchestrator import (
    _invoke_agent,
    compose_final_proposal,
    execute_plan,
    generate_plan,
)


@patch("core.orchestrator.complete")
def test_generate_plan_parses_llm_output(mock_complete):
    mock_complete.return_value = Mock(
        content='{"tasks": [{"role": "CTO", "title": "Plan", "summary": "Design"}]}'
    )
    tasks = generate_plan("new idea")
    assert tasks == [
        {"id": "T01", "role": "CTO", "title": "Plan", "description": "Design"}
    ]
    mock_complete.assert_called_once()


@patch("core.orchestrator._invoke_agent")
@patch("core.orchestrator.route_task")
def test_execute_plan_routes_and_invokes_agents(mock_route, mock_invoke):
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

    def side_effect(agent, idea, task, model=None):
        return f"{task['title']}-out"

    mock_invoke.side_effect = side_effect
    tasks = [
        {"role": "Research Scientist", "title": "t1", "description": "d1"},
        {"role": "Research Scientist", "title": "t2", "description": "d2"},
    ]
    answers = execute_plan("idea", tasks, agents={}, ui_model=None)
    assert answers["Research Scientist"] == "t1-out\n\nt2-out"
    assert mock_route.call_count == 2


def test_invoke_agent_handles_string_task():
    class DummyAgent:
        def run(self, context, task, model=None):
            assert isinstance(task, dict)
            return f"{task.get('title')}-{task.get('description')}"

    out = _invoke_agent(DummyAgent(), "ctx", "simple task")
    assert out == "simple task-simple task"


@patch("core.orchestrator.complete")
def test_compose_final_proposal_formats_findings(mock_complete):
    mock_complete.return_value = Mock(content=" final plan ")
    answers = {"CTO": "analysis"}
    result = compose_final_proposal("idea", answers)
    assert result == "final plan"
    system_prompt, prompt = mock_complete.call_args[0]
    assert "analysis" in prompt and "idea" in prompt
