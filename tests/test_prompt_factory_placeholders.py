import pytest

from config import feature_flags
from dr_rd.prompting.prompt_factory import PromptFactory
from dr_rd.prompting.prompt_registry import PromptRegistry, PromptTemplate, RetrievalPolicy


def make_factory():
    registry = PromptRegistry()
    registry.register(
        PromptTemplate(
            id="test",
            version="v1",
            role="Greeter",
            task_key=None,
            system="You are a friendly assistant.",
            user_template="Hello {{ name }}!",
            io_schema_ref="dr_rd/schemas/void.json",
            retrieval_policy=RetrievalPolicy.NONE,
        )
    )
    return PromptFactory(registry)


def test_missing_placeholder_raises(monkeypatch):
    monkeypatch.setattr(feature_flags, "SAFETY_ENABLED", False)
    monkeypatch.setattr(feature_flags, "RAG_ENABLED", False)
    monkeypatch.setattr(feature_flags, "ENABLE_LIVE_SEARCH", False)
    monkeypatch.setattr(feature_flags, "EXAMPLES_ENABLED", False)
    factory = make_factory()
    spec = {"role": "Greeter", "task": "", "inputs": {}}
    with pytest.raises(ValueError) as exc:
        factory.build_prompt(spec)
    assert ["name"] == str(exc.value).split(": ")[-1].split(", ")


def test_prompt_builds_when_all_placeholders_provided(monkeypatch):
    monkeypatch.setattr(feature_flags, "SAFETY_ENABLED", False)
    monkeypatch.setattr(feature_flags, "RAG_ENABLED", False)
    monkeypatch.setattr(feature_flags, "ENABLE_LIVE_SEARCH", False)
    monkeypatch.setattr(feature_flags, "EXAMPLES_ENABLED", False)
    factory = make_factory()
    spec = {"role": "Greeter", "task": "", "inputs": {"name": "Ada"}}
    prompt = factory.build_prompt(spec)
    assert prompt["user"] == "Hello Ada!"
    assert "system" in prompt
