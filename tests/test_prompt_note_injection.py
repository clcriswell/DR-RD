from dr_rd.prompting import PromptFactory
from dr_rd.prompting.prompt_registry import registry as default_registry

def test_placeholder_note_injection():
    factory = PromptFactory(default_registry)
    spec = {
        "role": "Planner",
        "task": "design a drone",
        "inputs": {
            "idea": "Discuss with [PERSON_1]",
            "constraints_section": "",
            "risk_section": "",
        },
    }
    result = factory.build_prompt(spec)
    assert "Placeholders like [PERSON_1], [ORG_1] are aliases. Use them verbatim." in result["system"]
