from core.agents.base_agent import LLMRoleAgent
from core.agents.hrm_agent import HRMAgent
from core.agents.planner_agent import PlannerAgent
from core.agents.reflection_agent import ReflectionAgent
from core.agents.chief_scientist_agent import ChiefScientistAgent
from core.agents.materials_engineer_agent import MaterialsEngineerAgent
from core.agents.regulatory_specialist_agent import RegulatorySpecialistAgent
from core.agents.registry import get_agent_class
from core.llm import select_model

MODEL = select_model("agent")

agents_dict = {
    "HRM": HRMAgent("HRM", MODEL),
    "Planner": PlannerAgent(MODEL),
    "Reflection": ReflectionAgent("Reflection", MODEL),
    "ChiefScientist": ChiefScientistAgent("ChiefScientist", MODEL),
    "MaterialsEngineer": MaterialsEngineerAgent("MaterialsEngineer", MODEL),
    "RegulatorySpecialist": RegulatorySpecialistAgent("RegulatorySpecialist", MODEL),
}

# Standard business roles via the central registry
for role, key in [("CTO", "CTO"), ("Research Scientist", "ResearchScientist")]:
    cls = get_agent_class(role)
    if cls:
        agents_dict[key] = cls(MODEL)
