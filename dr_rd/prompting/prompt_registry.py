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
            "gemini": {"function_declarations": "auto"},
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
            "gemini": {"function_declarations": "auto"},
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
        user_template="Summarize the following materials: {materials}",
        io_schema_ref="dr_rd/schemas/synthesizer_v1.json",
        retrieval_policy=RetrievalPolicy.NONE,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
            "gemini": {"function_declarations": "auto"},
        },
    )
)

# Additional role templates
registry.register(
    PromptTemplate(
        id="cto",
        version="v1",
        role="CTO",
        task_key=None,
        system="You are the CTO providing technical strategy and guidance.",
        user_template="Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/cto_v1.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
            "gemini": {"function_declarations": "auto"},
        },
    )
)

registry.register(
    PromptTemplate(
        id="regulatory",
        version="v1",
        role="Regulatory",
        task_key=None,
        system="You ensure projects meet regulatory and compliance requirements.",
        user_template="Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/regulatory_v1.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
            "gemini": {"function_declarations": "auto"},
        },
    )
)

registry.register(
    PromptTemplate(
        id="finance",
        version="v1",
        role="Finance",
        task_key=None,
        system="You are a financial analyst preparing budgets and cost estimates.",
        user_template="Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/finance_v1.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
            "gemini": {"function_declarations": "auto"},
        },
    )
)

registry.register(
    PromptTemplate(
        id="marketing",
        version="v1",
        role="Marketing Analyst",
        task_key=None,
        system="You perform market analysis and competitive research.",
        user_template="Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/marketing_v1.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
            "gemini": {"function_declarations": "auto"},
        },
    )
)

registry.register(
    PromptTemplate(
        id="ip_analyst",
        version="v1",
        role="IP Analyst",
        task_key=None,
        system="You investigate prior art and intellectual property strategy.",
        user_template="Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/ip_analyst_v1.json",
        retrieval_policy=RetrievalPolicy.AGGRESSIVE,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
            "gemini": {"function_declarations": "auto"},
        },
    )
)

registry.register(
    PromptTemplate(
        id="mechanical_systems_lead",
        version="v1",
        role="Mechanical Systems Lead",
        task_key=None,
        system="You design mechanical systems and assemblies.",
        user_template="Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/mechanical_systems_lead_v1.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
            "gemini": {"function_declarations": "auto"},
        },
    )
)

registry.register(
    PromptTemplate(
        id="hrm",
        version="v1",
        role="HRM",
        task_key=None,
        system="You identify human resource needs for the project.",
        user_template="Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/hrm_v1.json",
        retrieval_policy=RetrievalPolicy.NONE,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
            "gemini": {"function_declarations": "auto"},
        },
    )
)

registry.register(
    PromptTemplate(
        id="materials_engineer",
        version="v1",
        role="Materials Engineer",
        task_key=None,
        system="You evaluate material choices and manufacturing considerations.",
        user_template="Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/materials_engineer_v1.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
            "gemini": {"function_declarations": "auto"},
        },
    )
)

registry.register(
    PromptTemplate(
        id="reflection",
        version="v1",
        role="Reflection",
        task_key=None,
        system="You critique prior outputs and identify gaps.",
        user_template="Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/reflection_v1.json",
        retrieval_policy=RetrievalPolicy.NONE,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
            "gemini": {"function_declarations": "auto"},
        },
    )
)

registry.register(
    PromptTemplate(
        id="chief_scientist",
        version="v1",
        role="Chief Scientist",
        task_key=None,
        system="You integrate all domain findings into a cohesive plan.",
        user_template="Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/chief_scientist_v1.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
            "gemini": {"function_declarations": "auto"},
        },
    )
)

registry.register(
    PromptTemplate(
        id="regulatory_specialist",
        version="v1",
        role="Regulatory Specialist",
        task_key=None,
        system="You review ideas for safety and regulatory compliance.",
        user_template="Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/regulatory_specialist_v1.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
        provider_hints={
            "openai": {"json_mode": True, "tool_choice": "auto"},
            "anthropic": {"tool_choice": "auto"},
            "gemini": {"function_declarations": "auto"},
        },
    )
)
