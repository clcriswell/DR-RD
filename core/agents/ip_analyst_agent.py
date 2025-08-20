from core.agents.base_agent import BaseAgent
from config.feature_flags import RAG_ENABLED, RAG_TOPK
from dr_rd.utils.model_router import pick_model, CallHints
from dr_rd.utils.llm_client import log_usage
from dr_rd.llm_client import call_openai
from typing import Optional, Dict, Any, List, Tuple
import json
import re

try:
    from dr_rd.knowledge.retriever import Retriever  # type: ignore
    from dr_rd.knowledge.faiss_store import build_default_retriever  # type: ignore
except Exception:  # pragma: no cover
    Retriever = None  # type: ignore
    build_default_retriever = lambda: None  # type: ignore


class IPAnalystAgent(BaseAgent):
    """Agent for prior art scans, novelty checks and IP strategy."""

    def __init__(self, model: str, retriever: Optional[Retriever] = None):
        super().__init__(
            name="IP Analyst",
            model=model,
            system_message=(
                "You are an intellectual-property analyst skilled at prior-art searches, "
                "novelty assessment, patentability, and freedom-to-operate risk."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\nAs the IP Analyst, your task is {task}. "
                "Provide an IP analysis in Markdown. "
                "End with a JSON summary using keys: role, task, findings, risks, next_steps, sources."
            ),
            retriever=retriever,
        )

    def act(self, idea: str, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prompt = self.user_prompt_template.format(idea=idea, task=task)
        sources: List[str] = []
        hits: List[Tuple[str, str]] = []
        if RAG_ENABLED and self.retriever:
            try:
                hits = self.retriever.query(f"{idea}\n{task}", RAG_TOPK)
                if hits:
                    bundle_lines = []
                    for i, (text, src) in enumerate(hits, 1):
                        raw = text.replace("\n", " ")
                        bundle_lines.append(f"[{i}] {raw} ({src})")
                        sources.append(src)
                    bundle = "\n".join(bundle_lines)
                    prompt += "\n\n# RAG Knowledge\n" + bundle
            except Exception:
                hits = []
        self.retrieval_hits = len(hits)
        self.rag_text_len = sum(len(t.split()) for t, _ in hits)
        self._web_summary = None
        self._web_sources = []
        self.maybe_live_search(idea, task)
        if self._web_summary:
            prompt += "\n\n# Web Search Results\n" + self._web_summary
            prompt += (
                "\n\nIf you use Web Search Results, include a sources array in your JSON with short titles or URLs."
            )
            sources = self._web_sources or sources
        
        sel = pick_model(CallHints(stage="exec"))
        result = call_openai(
            model=sel["model"],
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ],
            **sel["params"],
        )
        resp = result["raw"]
        usage = getattr(resp, "usage", None)
        if usage is None and getattr(resp, "choices", None):
            usage = getattr(resp.choices[0], "usage", None)
        if usage:
            log_usage(
                stage="exec",
                model=sel["model"],
                pt=getattr(usage, "prompt_tokens", 0),
                ct=getattr(usage, "completion_tokens", 0),
            )
        raw = (result["text"] or "").strip()
        data: Dict[str, Any]
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception:
                    data = {
                        "role": self.name,
                        "task": task,
                        "findings": [raw],
                        "risks": [],
                        "next_steps": [],
                    }
            else:
                data = {
                    "role": self.name,
                    "task": task,
                    "findings": [raw],
                    "risks": [],
                    "next_steps": [],
                }
        data.setdefault("role", self.name)
        data.setdefault("task", task)
        data.setdefault("findings", [])
        data.setdefault("risks", [])
        data.setdefault("next_steps", [])
        if self._web_sources:
            data["sources"] = self._web_sources
        else:
            data.setdefault("sources", sources)
        return data
