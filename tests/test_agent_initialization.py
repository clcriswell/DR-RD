import pytest

from config.agent_models import AGENT_MODEL_MAP
from core.agents.ai_rd_coordinator_agent import AIResearchDevelopmentCoordinatorAgent
from core.agents.chemical_surface_science_specialist_agent import (
    ChemicalSurfaceScienceSpecialistAgent,
)
from core.agents.data_scientist_analytics_engineer_agent import (
    DataScientistAnalyticsEngineerAgent,
)
from core.agents.electronics_embedded_controls_engineer_agent import (
    ElectronicsEmbeddedControlsEngineerAgent,
)
from core.agents.fluorescence_biological_sample_expert_agent import (
    FluorescenceBiologicalSampleExpertAgent,
)
from core.agents.materials_process_engineer_agent import MaterialsProcessEngineerAgent
from core.agents.mechanical_precision_motion_engineer_agent import (
    MechanicalPrecisionMotionEngineerAgent,
)
from core.agents.mechanical_systems_lead_agent import MechanicalSystemsLeadAgent
from core.agents.nonlinear_optics_engineer_agent import NonlinearOpticsEngineerAgent
from core.agents.optical_systems_engineer_agent import OpticalSystemsEngineerAgent
from core.agents.photonics_electronics_engineer_agent import (
    PhotonicsElectronicsEngineerAgent,
)
from core.agents.product_manager_translational_lead_agent import (
    ProductManagerTranslationalLeadAgent,
)
from core.agents.project_manager_principal_investigator_agent import (
    ProjectManagerPrincipalInvestigatorAgent,
)
from core.agents.prototyping_test_lab_manager_agent import (
    PrototypingTestLabManagerAgent,
)
from core.agents.quantum_optics_physicist_agent import QuantumOpticsPhysicistAgent
from core.agents.regulatory_compliance_lead_agent import RegulatoryComplianceLeadAgent
from core.agents.software_image_processing_specialist_agent import (
    SoftwareImageProcessingSpecialistAgent,
)
from core.agents.systems_integration_validation_engineer_agent import (
    SystemsIntegrationValidationEngineerAgent,
)

AGENT_CLASSES = [
    ("Mechanical Systems Lead", MechanicalSystemsLeadAgent),
    ("Materials & Process Engineer", MaterialsProcessEngineerAgent),
    ("Chemical & Surface Science Specialist", ChemicalSurfaceScienceSpecialistAgent),
    ("Quantum Optics Physicist", QuantumOpticsPhysicistAgent),
    ("Nonlinear Optics / Crystal Engineer", NonlinearOpticsEngineerAgent),
    ("Optical Systems Engineer", OpticalSystemsEngineerAgent),
    ("Mechanical & Precision-Motion Engineer", MechanicalPrecisionMotionEngineerAgent),
    ("Photonics Electronics Engineer", PhotonicsElectronicsEngineerAgent),
    (
        "Electronics & Embedded Controls Engineer",
        ElectronicsEmbeddedControlsEngineerAgent,
    ),
    ("Software / Image-Processing Specialist", SoftwareImageProcessingSpecialistAgent),
    (
        "Fluorescence / Biological Sample Expert",
        FluorescenceBiologicalSampleExpertAgent,
    ),
    (
        "Systems Integration & Validation Engineer",
        SystemsIntegrationValidationEngineerAgent,
    ),
    ("Data Scientist / Analytics Engineer", DataScientistAnalyticsEngineerAgent),
    ("Regulatory & Compliance Lead", RegulatoryComplianceLeadAgent),
    ("Prototyping & Test Lab Manager", PrototypingTestLabManagerAgent),
    (
        "Project Manager / Principal Investigator",
        ProjectManagerPrincipalInvestigatorAgent,
    ),
    ("Product Manager / Translational Lead", ProductManagerTranslationalLeadAgent),
    ("AI R&D Coordinator", AIResearchDevelopmentCoordinatorAgent),
]


@pytest.mark.parametrize("role,cls", AGENT_CLASSES)
def test_agent_initialization(role, cls):
    model = AGENT_MODEL_MAP[role]
    agent = cls(model=model)
    assert agent.model == model
