from types import SimpleNamespace
from unittest.mock import patch
from dr_rd.retrieval.pipeline import ContextBundle
from core.agents.planner_agent import run_planner


def test_planner_inserts_reference():
    bundle = ContextBundle(rag_text="fact", web_summary="", sources=[])
    fake_resp = SimpleNamespace(choices=[], usage=SimpleNamespace(prompt_tokens=0, completion_tokens=0, total_tokens=0))
    with patch("core.agents.planner_agent.collect_context", return_value=bundle), patch(
        "core.agents.planner_agent.llm_call", return_value=fake_resp
    ) as mock_llm, patch("core.agents.planner_agent.extract_text", return_value="{\"tasks\": []}"):
        data, _ = run_planner("idea", "model")
        msgs = mock_llm.call_args[0][3]
        assert "Reference Knowledge" in msgs[1]["content"]
        assert data == {"tasks": []}
