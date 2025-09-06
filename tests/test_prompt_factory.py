import pytest

from dr_rd.prompting import PromptFactory
from dr_rd.prompting.prompt_registry import registry as default_registry
from config import feature_flags
import pytest


def test_template_resolution_and_provider_hints(monkeypatch):
    monkeypatch.setattr(feature_flags, "RAG_ENABLED", True)
    monkeypatch.setattr(feature_flags, "ENABLE_LIVE_SEARCH", True)
    factory = PromptFactory(default_registry)
    spec = {
        "role": "Planner",
        "task": "design a drone",
        "inputs": {
            "idea": "design a drone",
            "constraints_section": "",
            "risk_section": "",
        },
    }
    result = factory.build_prompt(spec)
    assert result["io_schema_ref"].endswith("planner_v1.json")
    assert result["retrieval_plan"]["policy"] == "LIGHT"
    assert "json" in result["system"].lower()
    assert "citation" in result["system"].lower()
    assert result["llm_hints"]["json_strict"] is True


def test_retrieval_disabled(monkeypatch):
    monkeypatch.setattr(feature_flags, "RAG_ENABLED", False)
    monkeypatch.setattr(feature_flags, "ENABLE_LIVE_SEARCH", False)
    factory = PromptFactory(default_registry)
    spec = {
        "role": "Planner",
        "task": "design a drone",
        "inputs": {
            "idea": "design a drone",
            "constraints_section": "",
            "risk_section": "",
        },
    }
    result = factory.build_prompt(spec)
    assert result["retrieval_plan"]["policy"] == "LIGHT"
    assert "citation" not in result["system"].lower()


def test_fallback_when_missing(monkeypatch):
    factory = PromptFactory(default_registry)
    spec = {
        "role": "Unknown",
        "task": "do something",
        "inputs": {
            "idea": "do something",
            "constraints_section": "",
            "risk_section": "",
        },
        "io_schema_ref": "dr_rd/schemas/custom.json",
    }
    result = factory.build_prompt(spec)
    assert result["io_schema_ref"] == "dr_rd/schemas/custom.json"
    assert result["retrieval_plan"]["policy"] == "NONE"
    assert "unknown" in result["system"].lower()


def test_missing_required_fields_raises():
    factory = PromptFactory(default_registry)
    spec = {
        "role": "Planner",
        "task": "design a drone",
        "inputs": {
            "constraints_section": "",
            "risk_section": "",
        },
    }
    with pytest.raises(ValueError) as exc:
        factory.build_prompt(spec)
    assert "idea" in str(exc.value)
