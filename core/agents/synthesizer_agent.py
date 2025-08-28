from __future__ import annotations

from typing import Any, Dict, List

from core.agents.prompt_agent import PromptFactoryAgent
from dr_rd.prompting.prompt_registry import RetrievalPolicy
from core.llm import select_model


class SynthesizerAgent(PromptFactoryAgent):
    def act(self, idea: str, answers: Dict[str, Any], **kwargs) -> str:
        materials = "\n".join(f"### {k}\n{v}" for k, v in answers.items())
        sources: List[Any] = []
        safety: List[Any] = []
        for val in answers.values():
            if isinstance(val, dict):
                for src in val.get("sources", []):
                    if src not in sources:
                        sources.append(src)
                if "safety_meta" in val:
                    safety.append(val["safety_meta"])
        spec = {
            "role": "Synthesizer",
            "task": "compose final report",
            "inputs": {"idea": idea, "materials": materials},
            "io_schema_ref": "dr_rd/schemas/synthesizer_v1.json",
            "retrieval_policy": RetrievalPolicy.NONE,
            "capabilities": "summary composer",
            "evaluation_hooks": ["self_check_minimal"],
        }
        result = super().run_with_spec(spec, **kwargs)
        if sources or safety:
            import json
            data = json.loads(result)
            if sources:
                data.setdefault("sources", [])
                data["sources"].extend(src for src in sources if src not in data["sources"])
            if safety:
                data["safety_meta"] = safety
                if any(m.get("decision", {}).get("allowed") is False for m in safety):
                    data.setdefault("contradictions", []).append("blocked content removed")
                    data["confidence"] = min(data.get("confidence", 1.0), 0.5)
            result = json.dumps(data)
        return result

    def run(self, idea: str, answers: Dict[str, Any], **kwargs) -> str:
        return self.act(idea, answers, **kwargs)


def compose_final_proposal(idea: str, answers: Dict[str, Any], model: str | None = None) -> str:
    agent = SynthesizerAgent(model or select_model("agent", agent_name="Synthesizer"))
    return agent.run(idea, answers)
