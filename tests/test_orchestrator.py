from unittest.mock import patch, Mock
import core.agents as core.agents.orchestrator as orch


def make_openai_response(text: str):
    mock_choice = Mock()
    mock_choice.message = Mock(content=text)
    return Mock(choices=[mock_choice])


@patch("core.agents.orchestrator.llm_call")
def test_needs_follow_up_returns_none(mock_llm):
    mock_llm.return_value = make_openai_response("COMPLETE")
    result = orch._needs_follow_up("Physics", "task", "answer")
    assert result is None


@patch("core.agents.orchestrator.llm_call")
def test_needs_follow_up_returns_question(mock_llm):
    mock_llm.return_value = make_openai_response(
        "Please clarify"
    )
    result = orch._needs_follow_up("Physics", "task", "answer")
    assert result == "Please clarify"


@patch("core.agents.orchestrator.route")
@patch("core.agents.orchestrator.obfuscate_task")
@patch("core.agents.orchestrator.llm_call")
def test_refine_once_no_follow_up(mock_llm, mock_obfuscate, mock_route):
    mock_llm.return_value = make_openai_response("COMPLETE")
    plan = {"Physics": "task1"}
    answers = {"Physics": "answer1"}
    result = orch.refine_once(plan, answers)
    assert result == answers
    mock_obfuscate.assert_not_called()
    mock_route.assert_not_called()


@patch("core.agents.orchestrator.route", return_value="extra info")
@patch("core.agents.orchestrator.obfuscate_task", return_value="obf")
@patch("core.agents.orchestrator.llm_call")
def test_refine_once_with_follow_up(mock_llm, mock_obfuscate, mock_route):
    mock_llm.return_value = make_openai_response(
        "More details?"
    )
    plan = {"Chemistry": "task2"}
    answers = {"Chemistry": "answer2"}
    result = orch.refine_once(plan, answers)
    expected = {"Chemistry": "answer2\n\n--- *(Loop-refined)* ---\nextra info"}
    assert result == expected
    mock_obfuscate.assert_called_once_with("Chemistry", "More details?")
    mock_route.assert_called_once_with("obf")
