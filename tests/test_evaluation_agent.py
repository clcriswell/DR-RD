import sys
from unittest.mock import patch

import config.feature_flags as ff
from core.agents.evaluation_agent import EvaluationAgent
from core.orchestrator import execute_plan


def make_streamlit():
    class ST:
        def __init__(self):
            self.session_state = {}
    return ST()


def test_evaluation_agent_sufficient():
    agent = EvaluationAgent()
    answers = {"Research Scientist": "Clear text with citation [1]."}
    payloads = {"Research Scientist": {"citations": ["a"], "findings": "done"}}
    context = {"rag_enabled": True}
    res = agent.run("idea", answers, payloads, context)
    assert res["insufficient"] is False
    assert res["followups"] == []


def test_evaluation_agent_followups():
    agent = EvaluationAgent()
    answers = {"Research Scientist": "TBD"}
    payloads = {"Research Scientist": {}}
    context = {"rag_enabled": True}
    res = agent.run("idea", answers, payloads, context)
    assert res["insufficient"] is True
    assert 0 < len(res["followups"]) <= 3


@patch("core.orchestrator.route_task")
@patch("core.orchestrator._invoke_agent")
def test_evaluation_loop_guard(mock_invoke, mock_route, monkeypatch):
    st = make_streamlit()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    monkeypatch.setattr("core.orchestrator.st", st)
    ff.EVALUATION_ENABLED = True
    ff.EVALUATION_HUMAN_REVIEW = False
    ff.EVALUATION_MAX_ROUNDS = 1
    class DummyAgent:
        def __init__(self, model):
            pass

    def fake_route(task, ui_model):
        return (
            task.get("role", "Research Scientist"),
            DummyAgent,
            "m1",
            task,
        )

    mock_route.side_effect = fake_route
    call_log = []

    def fake_invoke(agent, idea, task, model=None):
        call_log.append(task.get("title"))
        return "ok"

    mock_invoke.side_effect = fake_invoke

    iter_results = iter(
        [
            {
                "score": {},
                "insufficient": True,
                "findings": ["gap"],
                "followups": [{"role": "Research Scientist", "title": "F1", "description": "d"}],
                "notes": "",
                "metrics": {},
            },
            {
                "score": {},
                "insufficient": True,
                "findings": ["gap"],
                "followups": [{"role": "Research Scientist", "title": "F2", "description": "d"}],
                "notes": "",
                "metrics": {},
            },
        ]
    )

    monkeypatch.setattr(
        EvaluationAgent,
        "run",
        lambda self, idea, ans, payload, context=None: next(iter_results),
    )

    tasks = [{"role": "Research Scientist", "title": "t1", "description": "d1"}]
    execute_plan("idea", tasks, agents={})
    assert "t1" in call_log
    assert "F1" in call_log
    assert "F2" not in call_log


@patch("core.orchestrator.route_task")
@patch("core.orchestrator._invoke_agent")
def test_evaluation_human_review(mock_invoke, mock_route, monkeypatch):
    st = make_streamlit()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    monkeypatch.setattr("core.orchestrator.st", st)
    ff.EVALUATION_ENABLED = True
    ff.EVALUATION_HUMAN_REVIEW = True
    ff.EVALUATION_MAX_ROUNDS = 1
    class DummyAgent:
        def __init__(self, model):
            pass

    def fake_route(task, ui_model):
        return (
            task.get("role", "Research Scientist"),
            DummyAgent,
            "m1",
            task,
        )

    mock_route.side_effect = fake_route

    call_log = []

    def fake_invoke(agent, idea, task, model=None):
        call_log.append(task.get("title"))
        return "ok"

    mock_invoke.side_effect = fake_invoke
    monkeypatch.setattr(
        EvaluationAgent,
        "run",
        lambda self, idea, ans, payload, context=None: {
            "score": {},
            "insufficient": True,
            "findings": ["gap"],
            "followups": [{"role": "Research Scientist", "title": "F1", "description": "d"}],
            "notes": "",
            "metrics": {},
        },
    )
    tasks = [{"role": "Research Scientist", "title": "t1", "description": "d1"}]
    execute_plan("idea", tasks, agents={})
    assert st.session_state.get("awaiting_approval") is True
    assert st.session_state.get("pending_followups")[0]["title"] == "F1"
    assert all(title == "t1" for title in call_log)
