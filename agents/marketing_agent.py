from agents.base_agent import BaseAgent
from config.feature_flags import RAG_ENABLED, RAG_TOPK, RAG_SNIPPET_TOKENS
from dr_rd.utils.model_router import pick_model, CallHints
from dr_rd.utils.llm_client import llm_call, log_usage
from typing import Optional, Dict, Any, List, Tuple
import openai
import json
import re

try:
    from dr_rd.knowledge.retriever import Retriever  # type: ignore
    from dr_rd.knowledge.faiss_store import build_default_retriever  # type: ignore
except Exception:  # pragma: no cover
    Retriever = None  # type: ignore
    build_default_retriever = lambda: None  # type: ignore


class MarketingAgent(BaseAgent):
    """Agent performing market analysis, segmentation and competition review."""

    def __init__(self, model: str, retriever: Optional[Retriever] = None):
        super().__init__(
            name="Marketing Analyst",
            model=model,
            system_message=(
                "You are a marketing analyst with expertise in market research, "
                "customer segmentation, competitive landscapes and go-to-market strategies."
            ),
            user_prompt_template=(
                "Project Idea: {idea}\nAs the Marketing Analyst, your task is {task}. "
                "Provide a marketing overview in Markdown. "
                "End with a JSON summary using keys: role, task, findings, risks, next_steps, sources."
            ),
            retriever=retriever,
        )

    def act(self, idea: str, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prompt = self.user_prompt_template.format(idea=idea, task=task)
        sources: List[str] = []
        # Inject RAG snippets
        if RAG_ENABLED and self.retriever:
            try:
                hits: List[Tuple[str, str]] = self.retriever.query(f"{idea}\n{task}", RAG_TOPK)
                if hits:
                    bundle_lines = []
                    for i, (text, src) in enumerate(hits, 1):
                        raw = text.replace("\n", " ")
                        snippet = self._truncate_tokens(raw, RAG_SNIPPET_TOKENS)
                        bundle_lines.append(f"[{i}] {snippet} ({src})")
                        sources.append(src)
                    bundle = "\n".join(bundle_lines)
                    prompt += "\n\nResearch Bundle:\n" + bundle
            except Exception:
                pass
        
        sel = pick_model(CallHints(stage="exec"))
        response = llm_call(
            openai,
            sel["model"],
            stage="exec",
            messages=[
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt},
            ],
            **sel["params"],
        )
        usage = response.choices[0].usage if hasattr(response.choices[0], "usage") else getattr(response, "usage", None)
        if usage:
            log_usage(
                stage="exec",
                model=sel["model"],
                pt=getattr(usage, "prompt_tokens", 0),
                ct=getattr(usage, "completion_tokens", 0),
            )
        raw = response.choices[0].message.content.strip()
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
        data.setdefault("sources", sources)
        return data
