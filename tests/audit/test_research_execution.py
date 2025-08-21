import importlib
import inspect
from pathlib import Path

from tests.audit.fixtures import research_execution as fixtures


def test_agent_loop_controller_runs(monkeypatch):
    """Pass if run_pipeline executes one loop with stubbed agents."""
    orch = importlib.import_module("core.orchestrator")
    monkeypatch.setattr(orch, "PlannerAgent", fixtures.DummyPlanner)
    monkeypatch.setattr(orch, "build_agents", fixtures.dummy_build_agents)
    monkeypatch.setattr(orch, "synthesize", fixtures.dummy_synthesize)
    monkeypatch.setattr(orch, "load_mode_models", lambda mode: {"default": "gpt-5"})
    final, results, trace = orch.run_pipeline("idea")
    assert final == "stub dossier"
    assert results["Research Scientist"][0]["findings"] == ["stub"]
    assert trace[0]["agent"] == "Research Scientist"


def test_api_adapter_has_budget_tracking():
    """Pass if API adapter exposes token meter and budget hooks."""
    llm = importlib.import_module("core.llm_client")
    assert hasattr(llm, "TokenMeter")
    assert hasattr(llm, "BUDGET")


def test_dossier_builder_present():
    """Fail if dossier builder module is missing."""
    assert Path("src/dossier_builder.py").exists(), "dossier builder missing"


def test_gap_check_present():
    """Pass if orchestrator calls planner.revise_plan for gap checks."""
    orch = importlib.import_module("core.orchestrator")
    src = inspect.getsource(orch.run_pipeline)
    assert "revise_plan" in src


def test_dry_run_runbook_exists():
    """Fail if no dry-run runbook or config found."""
    runbook_paths = list(Path("docs").glob("*dry-run*")) + list(Path("config").glob("*dry*") )
    assert runbook_paths, "dry-run runbook missing"
