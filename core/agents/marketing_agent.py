import json
import re
from typing import Any, Dict, List, Optional, Tuple

from config.feature_flags import RAG_ENABLED, RAG_TOPK
from core.agents.base_agent import BaseAgent
from core.llm_client import call_openai, log_usage
from core.model_router import CallHints, pick_model
from dr_rd.retrieval.vector_store import Retriever
from prompts.prompts import MARKETING_SYSTEM_PROMPT, MARKETING_USER_PROMPT_TEMPLATE


class MarketingAgent(BaseAgent):
    """Agent performing market analysis, segmentation and competition review."""

    def __init__(self, model: str, retriever: Optional[Retriever] = None):
        super().__init__(
            name="Marketing Analyst",
            model=model,
            system_message=MARKETING_SYSTEM_PROMPT,
            user_prompt_template=MARKETING_USER_PROMPT_TEMPLATE,
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
                        bundle_lines.append(f"[{i}] {raw} ({src})")
                        sources.append(src)
                    bundle = "\n".join(bundle_lines)
                    prompt += "\n\nResearch Bundle:\n" + bundle
            except Exception:
                pass

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
        data.setdefault("sources", sources)
        return data
