from __future__ import annotations

from typing import Any, Dict, List

from core.agents.prompt_agent import PromptFactoryAgent
from dr_rd.prompting.prompt_registry import RetrievalPolicy


class SynthesizerAgent(PromptFactoryAgent):
    def act(self, idea: str, answers: Dict[str, Any], **kwargs) -> str:
        materials = "\n".join(f"### {k}\n{v}" for k, v in answers.items())
        sources: List[Any] = []
        for val in answers.values():
            if isinstance(val, dict):
                for src in val.get("sources", []):
                    if src not in sources:
                        sources.append(src)
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
        if sources:
            import json
            data = json.loads(result)
            data.setdefault("sources", [])
            data["sources"].extend(src for src in sources if src not in data["sources"])
            result = json.dumps(data)
        return result

    def run(self, idea: str, answers: Dict[str, Any], **kwargs) -> str:
        return self.act(idea, answers, **kwargs)
