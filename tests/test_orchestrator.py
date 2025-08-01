from unittest.mock import patch, Mock
import agents.orchestrator as orch


def make_openai_response(text: str):
    mock_choice = Mock()
    mock_choice.message = Mock(content=text)
    return Mock(choices=[mock_choice])


@patch('agents.orchestrator.openai')
def test_needs_follow_up_returns_none(mock_openai):
    mock_openai.chat.completions.create.return_value = make_openai_response("COMPLETE")
    result = orch._needs_follow_up('Physics', 'task', 'answer')
    assert result is None


@patch('agents.orchestrator.openai')
def test_needs_follow_up_returns_question(mock_openai):
    mock_openai.chat.completions.create.return_value = make_openai_response("Please clarify")
    result = orch._needs_follow_up('Physics', 'task', 'answer')
    assert result == "Please clarify"


@patch('agents.orchestrator.route')
@patch('agents.orchestrator.obfuscate_task')
@patch('agents.orchestrator.openai')
def test_refine_once_no_follow_up(mock_openai, mock_obfuscate, mock_route):
    mock_openai.chat.completions.create.return_value = make_openai_response("COMPLETE")
    plan = {'Physics': 'task1'}
    answers = {'Physics': 'answer1'}
    result = orch.refine_once(plan, answers)
    assert result == answers
    mock_obfuscate.assert_not_called()
    mock_route.assert_not_called()


@patch('agents.orchestrator.route', return_value='extra info')
@patch('agents.orchestrator.obfuscate_task', return_value='obf')
@patch('agents.orchestrator.openai')
def test_refine_once_with_follow_up(mock_openai, mock_obfuscate, mock_route):
    mock_openai.chat.completions.create.return_value = make_openai_response('More details?')
    plan = {'Chemistry': 'task2'}
    answers = {'Chemistry': 'answer2'}
    result = orch.refine_once(plan, answers)
    expected = {
        'Chemistry': 'answer2\n\n--- *(Loop-refined)* ---\nextra info'
    }
    assert result == expected
    mock_obfuscate.assert_called_once_with('Chemistry', 'More details?')
    mock_route.assert_called_once_with('Chemistry', 'obf')
