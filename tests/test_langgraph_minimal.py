import json
from unittest.mock import patch

import pytest

try:
    from core.graph import run_langgraph
except Exception:  # pragma: no cover - optional dependency
    run_langgraph = None


@pytest.mark.skipif(run_langgraph is None, reason="langgraph not installed")
def test_graph_runs_with_tool_request():
    provenance = []

    def fake_call_tool(agent, tool_name, params):
        provenance.append({"agent": agent, "tool": tool_name})
        return {"ok": True}

    def fake_get_provenance():
        return list(provenance)

    tasks = [
        {
            "id": "T1",
            "role": "Research Scientist",
            "title": "Run sim",
            "description": "",
            "tool_request": {"tool": "simulate", "params": {"inputs": {"a": 1.0}}},
        }
    ]

    with patch("core.orchestrator.generate_plan", return_value=tasks), patch(
        "core.router.route_task", side_effect=lambda t, ui_model=None: (t["role"], None, "m", t)
    ), patch(
        "core.router.dispatch",
        return_value=json.dumps({"result": "ok", "tool_request": tasks[0]["tool_request"]}),
    ), patch("core.orchestrator.compose_final_proposal", return_value={"document": "final"}), patch(
        "core.tool_router.call_tool", side_effect=fake_call_tool
    ), patch(
        "core.tool_router.get_provenance", side_effect=fake_get_provenance
    ):
        final, answers, trace_bundle = run_langgraph("idea", [], "low")

    assert answers["T1"]["tool_result"] == {"ok": True}
    nodes = [e["node"] for e in trace_bundle["trace"] if e["event"] == "start"]
    assert nodes == ["plan", "route", "agent", "tool", "collect", "synth"]
    assert final == "final"
