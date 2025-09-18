from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Dict, List

from core.agents.prompt_agent import PromptFactoryAgent, prepare_prompt_inputs
from core.agents.confidence import normalize_confidence
from dr_rd.prompting.prompt_registry import RetrievalPolicy
from core.llm import select_model
from dr_rd.telemetry import metrics


def _iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _iter_strings(nested)
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            yield from _iter_strings(nested)


def _normalize_scalar(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if "not determined" in stripped.casefold():
            return None
        return stripped
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return None


def _detect_conflicts(answers: Dict[str, Any]) -> List[str]:
    observations: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for module, payload in answers.items():
        if not isinstance(payload, dict):
            continue
        for field, raw_value in payload.items():
            if field in {"sources", "safety_meta", "retrieval_plan"}:
                continue
            normalized = _normalize_scalar(raw_value)
            if normalized is None:
                continue
            observations[field].append((module, normalized.casefold(), normalized))

    contradictions: List[str] = []
    for field, items in observations.items():
        groups: dict[str, dict[str, Any]] = {}
        for module, norm_key, original in items:
            bucket = groups.setdefault(norm_key, {"value": original, "modules": set()})
            bucket["modules"].add(module)
        if len(groups) > 1:
            parts: List[str] = []
            for bucket in groups.values():
                modules = ", ".join(sorted(bucket["modules"]))
                parts.append(f"{bucket['value']} ({modules})")
            contradictions.append(f"Conflicting {field}: " + " vs. ".join(parts))
    return contradictions


def _detect_placeholders(answers: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    for module, payload in answers.items():
        for text in _iter_strings(payload):
            lowered = text.casefold()
            if "not determined" in lowered:
                issues.append(f"{module} contains Not determined placeholder")
                break
            if "{{" in text and "}}" in text:
                issues.append(f"{module} contains unresolved template placeholders")
                break
    return issues


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
        inputs = prepare_prompt_inputs(task_scope, {"materials": materials}, idea=idea)
        spec = {
            "role": "Synthesizer",
            "task": "compose final report",
            "inputs": inputs,
            "io_schema_ref": "dr_rd/schemas/synthesizer_v1.json",
            "retrieval_policy": RetrievalPolicy.NONE,
            "capabilities": "summary composer",
            "evaluation_hooks": ["compartment_check", "self_check_minimal"],
        }
        result = super().run_with_spec(spec, **kwargs)
        data = json.loads(result)
        data["confidence"] = normalize_confidence(data.get("confidence", 1.0))
        contradictions = data.setdefault("contradictions", [])
        if sources:
            data.setdefault("sources", [])
            for src in sources:
                if src not in data["sources"]:
                    data["sources"].append(src)
        if safety:
            data["safety_meta"] = safety
            if any(m.get("decision", {}).get("allowed") is False for m in safety):
                message = "blocked content removed"
                if message not in contradictions:
                    contradictions.append(message)
                data["confidence"] = min(data.get("confidence", 1.0), 0.5)
        if missing_sources:
            message = "missing sources for " + ", ".join(missing_sources)
            if message not in contradictions:
                contradictions.append(message)
            data["confidence"] = min(data.get("confidence", 1.0), 0.7)
            metrics.inc("citations_missing", value=len(missing_sources), agent="Synthesizer")

        initial_count = len(contradictions)
        detected = _detect_conflicts(answers) + _detect_placeholders(answers)
        for message in detected:
            if message not in contradictions:
                contradictions.append(message)
        if len(contradictions) > initial_count and contradictions:
            data["confidence"] = min(data.get("confidence", 1.0), 0.6)

        return json.dumps(data)

    def run(self, idea: str, answers: Dict[str, Any], **kwargs) -> str:
        return self.act(idea, answers, **kwargs)


def compose_final_proposal(idea: str, answers: Dict[str, Any], model: str | None = None) -> str:
    agent = SynthesizerAgent(model or select_model("agent", agent_name="Synthesizer"))
    return agent.run(idea, answers)
