import json
import os
from unittest.mock import patch

import streamlit as st

from core import orchestrator
from core.agents import base_agent, prompt_agent, synthesizer_agent
from dr_rd.prompting.prompt_registry import RetrievalPolicy


@patch.dict(os.environ, {"OPENAI_API_KEY": "x"})
def test_compose_final_proposal_schema_enforcement(monkeypatch):
    stub_output = json.dumps(
        {
            "summary": "Overall results",
            "key_points": ["kp1"],
            "role": "Synthesizer",
            "task": "compose final report",
            "risks": ["r1"],
            "next_steps": ["n1"],
            "sources": [],
        }
    )

    monkeypatch.setattr(
        base_agent.LLMRoleAgent,
        "act",
        lambda self, system, user, **kwargs: stub_output,
    )

    def synth_act(self, idea, answers, **kwargs):
        materials = "\n".join(f"### {k}\n{v}" for k, v in answers.items())
        sources = []
        for val in answers.values():
            if isinstance(val, dict):
                sources.extend(val.get("sources", []))
            else:
                try:
                    obj = json.loads(val)
                    sources.extend(obj.get("sources", []))
                except Exception:
                    pass
        spec = {
            "role": "Synthesizer",
            "task": "compose final report",
            "inputs": {"idea": idea, "findings_md": materials},
            "io_schema_ref": "dr_rd/schemas/synthesizer_v1.json",
            "retrieval_policy": RetrievalPolicy.NONE,
            "capabilities": "summary composer",
            "evaluation_hooks": ["self_check_minimal"],
        }
        result = prompt_agent.PromptFactoryAgent.run_with_spec(self, spec, **kwargs)
        data = json.loads(result)
        if sources:
            data.setdefault("sources", []).extend(sources)
        return json.dumps(data)

    monkeypatch.setattr(synthesizer_agent.SynthesizerAgent, "act", synth_act)

    answers = {
        "Engineer": json.dumps(
            {
                "findings": "f1",
                "risks": ["ra"],
                "next_steps": ["na"],
                "sources": [{"url": "http://example.com"}],
            }
        )
    }

    st.session_state.clear()
    md = orchestrator.compose_final_proposal("idea", answers)
    for section in [
        "## Summary",
        "## Key Points",
        "## Findings",
        "## Risks",
        "## Next Steps",
        "## Sources",
    ]:
        assert section in md

    st.session_state.clear()

    def run_without_schema(self, spec, **kwargs):
        prompt = self._factory.build_prompt(spec)
        raw = base_agent.LLMRoleAgent.act(self, prompt["system"], prompt["user"], **kwargs)
        return prompt_agent.AgentRunResult(raw)

    monkeypatch.setattr(
        prompt_agent.PromptFactoryAgent, "run_with_spec", run_without_schema
    )
    md_no = orchestrator.compose_final_proposal("idea", answers)
    assert "## Summary" in md_no
    assert "## Findings" not in md_no
