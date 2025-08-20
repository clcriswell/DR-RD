from core.agents.planner_agent import PlannerAgent
from core.agents.mechanical_systems_lead_agent import MechanicalSystemsLeadAgent
from core.agents.materials_process_engineer_agent import MaterialsProcessEngineerAgent
from core.agents.chemical_surface_science_specialist_agent import ChemicalSurfaceScienceSpecialistAgent
from core.agents.quantum_optics_physicist_agent import QuantumOpticsPhysicistAgent
from core.agents.nonlinear_optics_engineer_agent import NonlinearOpticsEngineerAgent
from core.agents.optical_systems_engineer_agent import OpticalSystemsEngineerAgent
from core.agents.mechanical_precision_motion_engineer_agent import MechanicalPrecisionMotionEngineerAgent
from core.agents.photonics_electronics_engineer_agent import PhotonicsElectronicsEngineerAgent
from core.agents.electronics_embedded_controls_engineer_agent import ElectronicsEmbeddedControlsEngineerAgent
from core.agents.software_image_processing_specialist_agent import SoftwareImageProcessingSpecialistAgent
from core.agents.fluorescence_biological_sample_expert_agent import FluorescenceBiologicalSampleExpertAgent
from core.agents.systems_integration_validation_engineer_agent import SystemsIntegrationValidationEngineerAgent
from core.agents.data_scientist_analytics_engineer_agent import DataScientistAnalyticsEngineerAgent
from core.agents.regulatory_compliance_lead_agent import RegulatoryComplianceLeadAgent
from core.agents.prototyping_test_lab_manager_agent import PrototypingTestLabManagerAgent
from core.agents.project_manager_principal_investigator_agent import ProjectManagerPrincipalInvestigatorAgent
from core.agents.product_manager_translational_lead_agent import ProductManagerTranslationalLeadAgent
from core.agents.ai_rd_coordinator_agent import AIResearchDevelopmentCoordinatorAgent
from core.agents.synthesizer import SynthesizerAgent
from config.agent_models import AGENT_MODEL_MAP


def initialize_agents():
    photonics = PhotonicsElectronicsEngineerAgent(
        AGENT_MODEL_MAP["Photonics Electronics Engineer"]
    )
    return {
        "Planner": PlannerAgent(AGENT_MODEL_MAP["Planner"]),
        "Mechanical Systems Lead": MechanicalSystemsLeadAgent(
            AGENT_MODEL_MAP["Mechanical Systems Lead"]
        ),
        "Materials & Process Engineer": MaterialsProcessEngineerAgent(
            AGENT_MODEL_MAP["Materials & Process Engineer"]
        ),
        "Chemical & Surface Science Specialist": ChemicalSurfaceScienceSpecialistAgent(
            AGENT_MODEL_MAP["Chemical & Surface Science Specialist"]
        ),
        "Quantum Optics Physicist": QuantumOpticsPhysicistAgent(
            AGENT_MODEL_MAP["Quantum Optics Physicist"]
        ),
        "Nonlinear Optics / Crystal Engineer": NonlinearOpticsEngineerAgent(
            AGENT_MODEL_MAP["Nonlinear Optics / Crystal Engineer"]
        ),
        "Optical Systems Engineer": OpticalSystemsEngineerAgent(
            AGENT_MODEL_MAP["Optical Systems Engineer"]
        ),
        "Mechanical & Precision-Motion Engineer": MechanicalPrecisionMotionEngineerAgent(
            AGENT_MODEL_MAP["Mechanical & Precision-Motion Engineer"]
        ),
        "Photonics Electronics Engineer": photonics,
        "Photonic Electronics Engineer": photonics,
        "Electronics & Embedded Controls Engineer": ElectronicsEmbeddedControlsEngineerAgent(
            AGENT_MODEL_MAP["Electronics & Embedded Controls Engineer"]
        ),
        "Software / Image-Processing Specialist": SoftwareImageProcessingSpecialistAgent(
            AGENT_MODEL_MAP["Software / Image-Processing Specialist"]
        ),
        "Fluorescence / Biological Sample Expert": FluorescenceBiologicalSampleExpertAgent(
            AGENT_MODEL_MAP["Fluorescence / Biological Sample Expert"]
        ),
        "Systems Integration & Validation Engineer": SystemsIntegrationValidationEngineerAgent(
            AGENT_MODEL_MAP["Systems Integration & Validation Engineer"]
        ),
        "Data Scientist / Analytics Engineer": DataScientistAnalyticsEngineerAgent(
            AGENT_MODEL_MAP["Data Scientist / Analytics Engineer"]
        ),
        "Regulatory & Compliance Lead": RegulatoryComplianceLeadAgent(
            AGENT_MODEL_MAP["Regulatory & Compliance Lead"]
        ),
        "Prototyping & Test Lab Manager": PrototypingTestLabManagerAgent(
            AGENT_MODEL_MAP["Prototyping & Test Lab Manager"]
        ),
        "Project Manager / Principal Investigator": ProjectManagerPrincipalInvestigatorAgent(
            AGENT_MODEL_MAP["Project Manager / Principal Investigator"]
        ),
        "Product Manager / Translational Lead": ProductManagerTranslationalLeadAgent(
            AGENT_MODEL_MAP["Product Manager / Translational Lead"]
        ),
        "AI R&D Coordinator": AIResearchDevelopmentCoordinatorAgent(
            AGENT_MODEL_MAP["AI R&D Coordinator"]
        ),
        "Synthesizer": SynthesizerAgent(AGENT_MODEL_MAP["Synthesizer"]),
    }

