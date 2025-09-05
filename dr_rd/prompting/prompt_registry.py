"""Prompt templates and registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
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
    example_policy: Optional[Dict] = None


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
        key = (template.role, template.task_key)
        self._templates[key] = template

    def get(self, role: str, task_key: Optional[str] = None) -> Optional[PromptTemplate]:
        return self._templates.get((role, task_key)) or self._templates.get((role, None))

    def list(self, role: Optional[str] = None) -> List[PromptTemplate]:
        if role is None:
            return list(self._templates.values())
        return [tpl for (r, _), tpl in self._templates.items() if r == role]


registry = PromptRegistry()

# ---------------------------------------------------------------------------
# Legacy agent prompts
# ---------------------------------------------------------------------------

registry.register(
    PromptTemplate(
        id="planner",
        version="v1",
        role="Planner",
        task_key=None,
        system=(
            "You are the Planner. Output ONLY a JSON object of the form "
            '{"tasks":[...]}. Each task MUST contain non-empty strings: id, '
            "title, summary, description, role. Allowed roles: "
            '["CTO","Research Scientist","Regulatory","Finance","Marketing '
            'Analyst","IP Analyst","HRM","Materials Engineer","QA",'
            '"Simulation","Dynamic Specialist"]. Each task should include a '
            "brief description in 1–3 sentences and a role. Unknown domains "
            "should default to 'Dynamic Specialist'. Prefer ids "
            '"T01","T02",... If the user supplies ids, convert to that '
            "format. Produce at least six tasks spanning design/architecture, "
            "materials, regulatory/IP, finance, marketing, and QA/testing. "
            'If required information is missing, return {"error":"MISSING_INFO",'
            '"needs":[...]} instead of empty fields.'
        ),
        user_template=(
            "Project idea: {idea}{constraints_section}{risk_section}\n\n"
            "Follow the planner schema exactly and return only the JSON object. "
            "No extra text."
        ),
        io_schema_ref="dr_rd/schemas/planner_v1.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
    )
)

registry.register(
    PromptTemplate(
        id="synthesizer",
        version="v1",
        role="Synthesizer",
        task_key=None,
        system="You are a multi-disciplinary R&D lead.",
        user_template=(
            "**Goal**: “{idea}”\n\n"
            "We have gathered the following domain findings (some may include "
            'loop-refined addenda separated by "--- *(Loop-refined)* ---"):\n\n'
            "{findings_md}\n\n"
            "Write a comprehensive final report that brings together the "
            "project concept, researched data, and a build guide. Use clear "
            "Markdown with these sections:\n\n"
            "- ## Executive Summary\n"
            "- ## Problem & Value\n"
            "- ## Research Findings\n"
            "- ## Risks & Unknowns\n"
            "- ## Architecture & Interfaces\n"
            "- ## Regulatory & Compliance\n"
            "- ## IP & Prior Art\n"
            "- ## Market & GTM\n"
            "- ## Cost Overview\n"
            "- ## Next Steps"
        ),
        io_schema_ref="dr_rd/schemas/synthesizer_agent.json",
        retrieval_policy=RetrievalPolicy.NONE,
    )
)

registry.register(
    PromptTemplate(
        id="cto",
        version="v1",
        role="CTO",
        task_key=None,
        system=(
            "You are the CTO. Assess feasibility, architecture, and risks. "
            "Return clear, structured guidance and conclude with a JSON summary "
            "using keys: role, task, findings, risks, next_steps, sources."
        ),
        user_template="Project Idea:\n{idea}\n\nTask:\n{task}",
        io_schema_ref="dr_rd/schemas/cto_agent.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
    )
)

registry.register(
    PromptTemplate(
        id="regulatory",
        version="v1",
        role="Regulatory",
        task_key=None,
        system=(
            "You are a regulatory compliance expert with knowledge of industry "
            "standards and laws. You provide detailed compliance analysis, "
            "referencing standards and guidelines. You justify how the design "
            "meets (or needs modifications to meet) each requirement and adjust "
            "recommendations if testing/simulation reveals new issues."
        ),
        user_template=(
            "Project Idea: {idea}\n"
            "As the Regulatory expert, your task is {task}. Provide a thorough "
            "analysis of regulatory requirements and compliance steps in "
            "Markdown format, including any certifications or standards needed, "
            "and mapping of system components to regulations. Include "
            "justification for each compliance recommendation (e.g., why a "
            "certain standard applies). Conclude with a JSON summary using "
            "keys: role, task, findings, risks, next_steps, sources."
        ),
        io_schema_ref="dr_rd/schemas/regulatory_agent.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
    )
)

registry.register(
    PromptTemplate(
        id="finance",
        version="v1",
        role="Finance",
        task_key=None,
        system="You evaluate budgets, BOM costs and financial risks.",
        user_template=(
            "Project Idea: {idea}\n"
            "As the Finance lead, your task is {task}. Conclude with a JSON "
            "summary using keys: role, task, findings, risks, next_steps, "
            "sources."
        ),
        io_schema_ref="dr_rd/schemas/finance_agent.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
    )
)

registry.register(
    PromptTemplate(
        id="marketing",
        version="v1",
        role="Marketing Analyst",
        task_key=None,
        system=(
            "You are a marketing analyst with expertise in market research, "
            "customer segmentation, competitive landscapes and go-to-market "
            "strategies."
        ),
        user_template=(
            "Project Idea: {idea}\n"
            "As the Marketing Analyst, your task is {task}. Provide a marketing "
            "overview in Markdown. End with a JSON summary using keys: role, "
            "task, findings, risks, next_steps, sources."
        ),
        io_schema_ref="dr_rd/schemas/marketing_agent.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
    )
)

registry.register(
    PromptTemplate(
        id="ip_analyst",
        version="v1",
        role="IP Analyst",
        task_key=None,
        system=(
            "You are an intellectual-property analyst skilled at prior-art "
            "searches, novelty assessment, patentability, and freedom-to-operate "
            "risk."
        ),
        user_template=(
            "Project Idea: {idea}\n"
            "As the IP Analyst, your task is {task}. Provide an IP analysis in "
            "Markdown. End with a JSON summary using keys: role, task, "
            "findings, risks, next_steps, sources."
        ),
        io_schema_ref="dr_rd/schemas/ip_analyst_agent.json",
        retrieval_policy=RetrievalPolicy.AGGRESSIVE,
    )
)

registry.register(
    PromptTemplate(
        id="patent",
        version="v1",
        role="Patent",
        task_key=None,
        system=(
            "You are a patent attorney and innovation expert focusing on "
            "intellectual property. You thoroughly analyze existing patents and "
            "technical disclosures, referencing diagrams or figures if relevant. "
            "You justify your conclusions on patentability and can adjust IP "
            "strategy if new technical feedback warrants it."
        ),
        user_template=(
            "Project Idea: {idea}\n"
            "As the Patent expert, your task is {task}. Provide an analysis in "
            "Markdown format of patentability, including any existing patents "
            "(with relevant patent figures or diagrams if applicable) and an IP "
            "strategy. Include reasoning behind each recommendation (e.g., why "
            "certain features are patentable or not). Conclude with a JSON "
            "summary using keys: role, task, findings, risks, next_steps, "
            "sources."
        ),
        io_schema_ref="dr_rd/schemas/patent_agent.json",
        retrieval_policy=RetrievalPolicy.AGGRESSIVE,
    )
)

registry.register(
    PromptTemplate(
        id="research_scientist",
        version="v1",
        role="Research Scientist",
        task_key=None,
        system=(
            "You are the Research Scientist. Provide specific, non-generic "
            "analysis with concrete details. Conclude with a JSON summary using "
            "keys: role, task, findings, risks, next_steps, sources."
        ),
        user_template="Project Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/research_scientist_agent.json",
        retrieval_policy=RetrievalPolicy.AGGRESSIVE,
    )
)

registry.register(
    PromptTemplate(
        id="hrm",
        version="v1",
        role="HRM",
        task_key=None,
        system=(
            "You are an HR Manager specializing in R&D projects. Identify the "
            "expert roles needed for the following idea. Conclude with a JSON "
            "summary using keys: role, task, findings, risks, next_steps, "
            "sources."
        ),
        user_template="Project Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/hrm_agent.json",
        retrieval_policy=RetrievalPolicy.NONE,
    )
)

registry.register(
    PromptTemplate(
        id="materials_engineer",
        version="v1",
        role="Materials Engineer",
        task_key=None,
        system=(
            "You are a Materials Engineer specialized in material selection and "
            "engineering feasibility. Conclude with a JSON summary using keys: "
            "role, task, findings, risks, next_steps, sources."
        ),
        user_template="Project Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/materials_engineer_agent.json",
        retrieval_policy=RetrievalPolicy.LIGHT,
    )
)

registry.register(
    PromptTemplate(
        id="reflection",
        version="v1",
        role="Reflection",
        task_key=None,
        system=(
            "You are a Reflection agent analyzing the team's outputs. Determine "
            "if follow-up tasks are required. Respond with either a JSON array "
            "of follow-up task strings or the exact string 'no further tasks'."
        ),
        user_template="Project Idea: {idea}\nTask: {task}",
        io_schema_ref="dr_rd/schemas/reflection_agent.json",
        retrieval_policy=RetrievalPolicy.NONE,
    )
)


__all__ = [
    "PromptTemplate",
    "PromptRegistry",
    "RetrievalPolicy",
    "RETRIEVAL_POLICY_META",
    "RETRIEVAL_NONE",
    "RETRIEVAL_LIGHT",
    "RETRIEVAL_AGGRESSIVE",
    "registry",
]
