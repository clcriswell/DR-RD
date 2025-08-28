from core.agents.base_agent import BaseAgent

"""Regulatory & Compliance Lead Agent for regulatory strategy and adherence."""


class RegulatoryComplianceLeadAgent(BaseAgent):
    """Agent ensuring projects satisfy relevant regulations and standards."""

    def __init__(self, model):
        super().__init__(
            name="Regulatory & Compliance Lead",
            model=model,
            system_message=(
                # Schema: dr_rd/schemas/regulatory_compliance_lead_agent.json
                "You are a regulatory and compliance lead well-versed in industry standards, "
                "safety regulations, and certification processes (e.g., FDA, OSHA, ISO). "
                "You ensure the project meets all necessary regulatory requirements efficiently, "
                "identifying what documentation or tests are needed for compliance. "
                "You keep the team informed of any regulatory hurdles and how to overcome them early on."
            ),
            user_prompt_template=(
                # Schema: dr_rd/schemas/regulatory_compliance_lead_agent.json
                "Project Idea: {idea}\\n"
                "As the Regulatory & Compliance Lead, your task is {task}. "
                "Provide a comprehensive compliance strategy in Markdown, identifying relevant regulations/"
                "standards and outlining steps to ensure the project adheres to them. "
                "List any required certifications or safety standards (e.g., ISO standards, OSHA guidelines, "
                "FDA approvals) and describe how the design will meet each. Include recommendations for "
                "documentation or testing needed to verify compliance. Conclude with a JSON list of key "
                "regulatory requirements and the planned compliance actions for each."
            ),
        )
