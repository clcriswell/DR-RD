import os
from core.agents.base_agent import LLMRoleAgent
from core.agents.hrm_agent import HRMAgent
from core.agents.planner_agent import PlannerAgent
from core.agents.reflection_agent import ReflectionAgent
from core.agents.chief_scientist_agent import ChiefScientistAgent
from core.agents.cto_agent import CTOAgent
from core.agents.research_scientist_agent import ResearchScientistAgent
from core.agents.materials_engineer_agent import MaterialsEngineerAgent
from core.agents.regulatory_specialist_agent import RegulatorySpecialistAgent

MODEL = os.getenv("OPENAI_MODEL", "gpt-5").strip()

agents_dict = {
    "HRM": HRMAgent("HRM", MODEL),
    "Planner": PlannerAgent("Planner", MODEL),
    "Reflection": ReflectionAgent("Reflection", MODEL),
    "ChiefScientist": ChiefScientistAgent("ChiefScientist", MODEL),
    "CTO": CTOAgent("CTO", MODEL),
    "ResearchScientist": ResearchScientistAgent("ResearchScientist", MODEL),
    "MaterialsEngineer": MaterialsEngineerAgent("MaterialsEngineer", MODEL),
    "RegulatorySpecialist": RegulatorySpecialistAgent("RegulatorySpecialist", MODEL),
}
