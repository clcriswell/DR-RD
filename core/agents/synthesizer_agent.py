from __future__ import annotations

from typing import Any, Dict, List

from core.agents.prompt_agent import PromptFactoryAgent, prepare_prompt_inputs
from core.agents.confidence import normalize_confidence
from dr_rd.prompting.prompt_registry import RetrievalPolicy
from core.llm import select_model
from dr_rd.telemetry import metrics


class SynthesizerAgent(PromptFactoryAgent):
    def act(self, idea: str, answers: Dict[str, Any], **kwargs) -> str:
        materials = "\n".join(f"### {k}\n{v}" for k, v in answers.items())
        sources: List[Any] = []
        safety: List[Any] = []
        missing_sources: List[str] = []
        seen = set()
        for key, val in answers.items():
            if isinstance(val, dict):
                if val.get("retrieval_plan") and not val.get("sources"):
                    missing_sources.append(key)
                for src in val.get("sources", []):
                    # src may be a dict or a direct URL string
                    if isinstance(src, dict):
                        url = src.get("url", "")
                    else:
                        url = src  # assume string is already a URL
                    canon = url.split("#")[0].rstrip("/")
                    if canon in seen:
                        continue
                    seen.add(canon)
                    sources.append(src)
                if "safety_meta" in val:
                    safety.append(val["safety_meta"])
        task_scope = {
            "description": "compose final report",
            "inputs": list(answers.keys()),
            "outputs": ["Final synthesis"],
            "constraints": [],
        }
        inputs = prepare_prompt_inputs(task_scope, {"materials": materials})
        spec = {
            "role": "Synthesizer",
            "task": "compose final report",
            "inputs": inputs,
            "io_schema_ref": "dr_rd/schemas/synthesizer_v1.json",
            "retrieval_policy": RetrievalPolicy.NONE,
            "capabilities": "summary composer",
            "evaluation_hooks": ["self_check_minimal"],
        }
        result = super().run_with_spec(spec, **kwargs)
        if sources or safety or missing_sources:
            import json
            data = json.loads(result)
            # Always normalize confidence to a numeric value for downstream math
            data["confidence"] = normalize_confidence(data.get("confidence", 1.0))
            if sources:
                data.setdefault("sources", [])
                for src in sources:
                    if src not in data["sources"]:
                        data["sources"].append(src)
            if safety:
                data["safety_meta"] = safety
                if any(m.get("decision", {}).get("allowed") is False for m in safety):
                    data.setdefault("contradictions", []).append("blocked content removed")
                    data["confidence"] = min(data.get("confidence", 1.0), 0.5)
            if missing_sources:
                data.setdefault("contradictions", []).append("missing sources for " + ", ".join(missing_sources))
                data["confidence"] = min(data.get("confidence", 1.0), 0.7)
                metrics.inc("citations_missing", value=len(missing_sources), agent="Synthesizer")
            result = json.dumps(data)
        return result

    def run(self, idea: str, answers: Dict[str, Any], **kwargs) -> str:
        return self.act(idea, answers, **kwargs)


def compose_final_proposal(idea: str, answers: Dict[str, Any], model: str | None = None) -> str:
    agent = SynthesizerAgent(model or select_model("agent", agent_name="Synthesizer"))
    return agent.run(idea, answers)
