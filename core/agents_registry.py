from agents.hrm_agent import HRMAgent
from agents.planner_agent import LLMPlannerAgent
from agents.reflection_agent import ReflectionAgent
from agents.chief_scientist_agent import ChiefScientistAgent
from agents.cto_agent import SimpleCTOAgent
from agents.research_scientist_agent import ResearchScientistAgent
from agents.materials_engineer_agent import MaterialsEngineerAgent
from agents.regulatory_specialist_agent import RegulatorySpecialistAgent

DEFAULT_MODEL = "gpt-4o-mini"

agents_dict = {
    "HRM": HRMAgent(DEFAULT_MODEL),
    "Planner": LLMPlannerAgent(DEFAULT_MODEL),
    "Reflection": ReflectionAgent(DEFAULT_MODEL),
    "ChiefScientist": ChiefScientistAgent(DEFAULT_MODEL),
    "CTO": SimpleCTOAgent(DEFAULT_MODEL),
    "ResearchScientist": ResearchScientistAgent(DEFAULT_MODEL),
    "MaterialsEngineer": MaterialsEngineerAgent(DEFAULT_MODEL),
    "RegulatorySpecialist": RegulatorySpecialistAgent(DEFAULT_MODEL),
}
