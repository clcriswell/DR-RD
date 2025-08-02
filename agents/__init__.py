from agents.planner_agent import PlannerAgent
from agents.cto_agent import CTOAgent
from agents.research_scientist_agent import ResearchScientistAgent
from agents.engineer_agent import EngineerAgent
from agents.qa_agent import QAAgent
from agents.regulatory_agent import RegulatoryAgent
from agents.patent_agent import PatentAgent
from agents.documentation_agent import DocumentationAgent
from agents.sustainability_agent import SustainabilityAgent
from config.agent_models import AGENT_MODEL_MAP

# Pass each agent its designated model

def initialize_agents():
    return {
        "Planner": PlannerAgent(AGENT_MODEL_MAP["Planner"]),
        "CTO": CTOAgent(AGENT_MODEL_MAP["CTO"]),
        "Research Scientist": ResearchScientistAgent(AGENT_MODEL_MAP["Research Scientist"]),
        "Engineer": EngineerAgent(AGENT_MODEL_MAP["Engineer"]),
        "QA Specialist": QAAgent(AGENT_MODEL_MAP["QA Specialist"]),
        "Regulatory Specialist": RegulatoryAgent(AGENT_MODEL_MAP["Regulatory Specialist"]),
        "Patent Specialist": PatentAgent(AGENT_MODEL_MAP["Patent Specialist"]),
        "Documentation Specialist": DocumentationAgent(AGENT_MODEL_MAP["Documentation Specialist"]),
        "Sustainability Specialist": SustainabilityAgent(AGENT_MODEL_MAP["Sustainability Specialist"]),
    }
