import pytest

from dr_rd.prompting import PromptFactory


@pytest.fixture
def prompt_factory(monkeypatch):
    from config import feature_flags

    monkeypatch.setattr(feature_flags, "SAFETY_ENABLED", False, raising=False)
    monkeypatch.setattr(feature_flags, "FILTERS_STRICT_MODE", False, raising=False)
    monkeypatch.setattr(feature_flags, "RAG_ENABLED", False, raising=False)
    monkeypatch.setattr(feature_flags, "ENABLE_LIVE_SEARCH", False, raising=False)
    monkeypatch.setattr(feature_flags, "EXAMPLES_ENABLED", False, raising=False)
    return PromptFactory()


def _iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)


@pytest.mark.parametrize(
    "role",
    [
        "CTO",
        "Regulatory",
        "Finance",
        "Marketing Analyst",
        "IP Analyst",
        "Materials Engineer",
        "QA",
    ],
)
def test_no_idea_in_agent_prompts(prompt_factory, role):
    secret_idea = "Project LANTERN"
    spec = {
        "role": role,
        "task": "Neutral execution task",
        "inputs": {
            "task_description": "Evaluate subsystem requirements",
            "task_inputs": ["Sensor benchmarks"],
            "task_outputs": ["Feasibility assessment"],
            "task_constraints": ["Budget ceiling"],
            "idea": secret_idea,
        },
    }

    prompt = prompt_factory.build_prompt(spec)
    user_prompt = prompt["user"]

    assert "Task description: Evaluate subsystem requirements" in user_prompt
    assert "Inputs: Sensor benchmarks" in user_prompt
    assert "Outputs: Feasibility assessment" in user_prompt
    assert "Constraints: Budget ceiling" in user_prompt

    for text in _iter_strings(prompt):
        lowered = text.lower()
        assert "idea:" not in text
        assert secret_idea.lower() not in lowered
        assert "project idea" not in lowered
