"""Prompt templates and registry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


@dataclass
class PromptTemplate:
    """Represents a prompt template and associated metadata."""

    id: str
    version: str
    role: str
    task_key: Optional[str]
    system: str
    user_template: str
    io_schema_ref: str
    retrieval_policy: "RetrievalPolicy"
    evaluation_hooks: Optional[List[str]] = None
    safety_notes: Optional[str] = None
    provider_hints: Optional[Dict] = None
    examples_ref: Optional[str] = None


class RetrievalPolicy(Enum):
    """Defines retrieval aggressiveness."""

    NONE = "NONE"
    LIGHT = "LIGHT"
    AGGRESSIVE = "AGGRESSIVE"


RETRIEVAL_POLICY_META = {
    RetrievalPolicy.NONE: {"top_k": 0, "source_types": [], "budget_hint": "none"},
    RetrievalPolicy.LIGHT: {
        "top_k": 5,
        "source_types": ["web", "local"],
        "budget_hint": "conservative",
    },
    RetrievalPolicy.AGGRESSIVE: {
        "top_k": 10,
        "source_types": ["web", "academic", "local"],
        "budget_hint": "generous",
    },
}

RETRIEVAL_NONE = RetrievalPolicy.NONE
RETRIEVAL_LIGHT = RetrievalPolicy.LIGHT
RETRIEVAL_AGGRESSIVE = RetrievalPolicy.AGGRESSIVE


class PromptRegistry:
    """Registry for prompt templates."""

    def __init__(self) -> None:
        self._templates: Dict[Tuple[str, Optional[str]], PromptTemplate] = {}

    def register(self, template: PromptTemplate) -> None:
        """Register or overwrite a prompt template."""

        key = (template.role, template.task_key)
        self._templates[key] = template

    def get(self, role: str, task_key: Optional[str] = None) -> Optional[PromptTemplate]:
        """Retrieve a template by role and optional task key."""

        return self._templates.get((role, task_key)) or self._templates.get((role, None))

    def list(self, role: Optional[str] = None) -> List[PromptTemplate]:
        """List registered templates, optionally filtered by role."""

        if role is None:
            return list(self._templates.values())
        return [tpl for (r, _), tpl in self._templates.items() if r == role]

    def as_dict(self) -> Dict:
        """Return a serialisable representation for debugging."""

        result: Dict = {}
        for (role, task_key), tpl in self._templates.items():
            result.setdefault(role, {})[task_key or "default"] = asdict(tpl)
        return result


# Global registry seeded with initial templates ---------------------------------
registry = PromptRegistry()

registry.register(
    PromptTemplate(
        id="planner",
        version="v1",
        role="Planner",
        task_key=None,
        system="You are the planning agent responsible for drafting project plans.",
        user_template="Develop a plan for the following goal: {task}",
        io_schema_ref="dr_rd/schemas/planner_v1.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
        },
    )
)

registry.register(
    PromptTemplate(
        id="research",
        version="v1",
        role="Research Scientist",
        task_key=None,
        system="You are a research scientist uncovering facts and evidence.",
        user_template="Investigate the following question: {task}",
        io_schema_ref="dr_rd/schemas/research_v1.json",
        retrieval_policy=RetrievalPolicy.AGGRESSIVE,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
        },
    )
)

registry.register(
    PromptTemplate(
        id="synthesizer",
        version="v1",
        role="Synthesizer",
        task_key=None,
        system="You synthesize plans and findings into coherent summaries.",
        user_template="Summarize the following materials: {task}",
        io_schema_ref="dr_rd/schemas/synthesizer_v1.json",
        retrieval_policy=RetrievalPolicy.NONE,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
        },
    )
)
