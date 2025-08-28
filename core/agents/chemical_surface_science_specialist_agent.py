from core.agents.base_agent import BaseAgent

"""Chemical & Surface Science Specialist Agent focusing on surface chemistry and treatments."""


class ChemicalSurfaceScienceSpecialistAgent(BaseAgent):
    """Agent that optimizes surface properties through chemical and coating techniques."""

    def __init__(self, model):
        super().__init__(
            name="Chemical & Surface Science Specialist",
            model=model,
            system_message=(
                # Schema: dr_rd/schemas/chemical_surface_science_specialist_agent.json
                "You are a chemical and surface science specialist knowledgeable in coatings, surface treatments, and chemical durability. "
                "You focus on ensuring materials have proper surface properties (e.g., adhesion, corrosion resistance, hydrophobicity) and can withstand environmental factors. "
                "You optimize surface processes for longevity and performance."
            ),
            user_prompt_template=(
                # Schema: dr_rd/schemas/chemical_surface_science_specialist_agent.json
                "Project Idea: {idea}\nAs the Chemical & Surface Science Specialist, your task is {task}. "
                "Provide a detailed plan in Markdown for surface treatments and chemical processes to enhance the project's materials. "
                "Recommend surface coatings or treatments (with details like thickness or composition) to improve durability and resistance (e.g., to UV, corrosion, chemicals). "
                "Include predictions of coating performance and expected lifetimes under various conditions. "
                "Conclude with a JSON list of recommended surface treatments and their key properties (e.g., type, expected durability)."
            ),
        )
