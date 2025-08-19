import os
from agents.base_agent import LLMRoleAgent
from agents.hrm_agent import HRMAgent
from agents.planner_agent import PlannerAgent
from agents.reflection_agent import ReflectionAgent
from agents.chief_scientist_agent import ChiefScientistAgent
from agents.cto_agent import CTOAgent
from agents.research_scientist_agent import ResearchScientistAgent
from agents.materials_engineer_agent import MaterialsEngineerAgent
from agents.regulatory_specialist_agent import RegulatorySpecialistAgent

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

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
