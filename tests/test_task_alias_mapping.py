from core.schemas import Task


def test_task_alias_mapping_role_objective():
    t = Task.model_validate({"id": "1", "role": "CTO", "objective": "Assess architecture"})
    assert t.title == "CTO"
    assert t.summary == "Assess architecture"


def test_task_alias_mapping_name_description():
    t = Task.model_validate(
        {"id": "2", "name": "Research Scientist", "description": "Study feasibility"}
    )
    assert t.title == "Research Scientist"
    assert t.summary == "Study feasibility"
