from unittest.mock import patch, Mock

from core.orchestrator import generate_plan, execute_plan, compile_proposal


@patch("core.orchestrator.complete")
def test_generate_plan_parses_llm_output(mock_complete):
    mock_complete.return_value = Mock(
        content='[{"role": "CTO", "title": "Plan", "description": "Design"}]'
    )
    tasks = generate_plan("new idea")
    assert tasks == [
        {"role": "CTO", "title": "Plan", "description": "Design"}
    ]
    mock_complete.assert_called_once()


@patch("core.orchestrator._invoke_agent")
@patch("core.orchestrator.choose_agent_for_task")
def test_execute_plan_routes_and_invokes_agents(mock_choose, mock_invoke):
    class DummyAgent:
        def __init__(self, model):
            self.model = model

    mock_choose.return_value = ("Research Scientist", DummyAgent)

    def side_effect(agent, idea, task):
        return f"{task['title']}-out"

    mock_invoke.side_effect = side_effect
    tasks = [
        {"role": "Research Scientist", "title": "t1", "description": "d1"},
        {"role": "Research Scientist", "title": "t2", "description": "d2"},
    ]
    answers = execute_plan("idea", tasks)
    assert answers["Research Scientist"] == "t1-out\n\nt2-out"
    assert mock_choose.call_count == 2


@patch("core.orchestrator.complete")
def test_compile_proposal_formats_findings(mock_complete):
    mock_complete.return_value = Mock(content=" final plan ")
    answers = {"CTO": "analysis"}
    result = compile_proposal("idea", answers)
    assert result == "final plan"
    system_prompt, prompt = mock_complete.call_args[0]
    assert "analysis" in prompt and "idea" in prompt
