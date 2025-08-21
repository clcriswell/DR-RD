import importlib
import inspect
import json
from pathlib import Path

from tests.audit.fixtures import research_execution as fixtures


def test_agent_loop_controller_runs(monkeypatch, tmp_path):
    """Pass if run_pipeline executes one loop with stubbed agents and saves dossier."""
    orch = importlib.import_module("core.orchestrator")
    monkeypatch.setattr(orch, "PlannerAgent", fixtures.DummyPlanner)
    monkeypatch.setattr(orch, "build_agents", fixtures.dummy_build_agents)
    monkeypatch.setattr(orch, "synthesize", fixtures.dummy_synthesize)
    monkeypatch.setattr(orch, "load_mode_models", lambda mode: {"default": "gpt-5"})
    final, results, trace = orch.run_pipeline("idea", runs_dir=tmp_path)
    assert final == "stub dossier"
    assert results["Research Scientist"][0]["findings"] == ["stub"]
    assert trace[0]["agent"] == "Research Scientist"
    dossier_files = list(tmp_path.rglob("dossier.json"))
    assert dossier_files, "dossier not saved"
    with open(dossier_files[0], "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["findings"][0]["body"] == "stub"


def test_api_adapter_has_budget_tracking():
    """Pass if API adapter exposes token meter and budget hooks."""
    llm = importlib.import_module("core.llm_client")
    assert hasattr(llm, "TokenMeter")
    assert hasattr(llm, "BUDGET")


def test_dossier_builder_present():
    """Pass if dossier builder records findings with evidences."""
    dossier_module = importlib.import_module("core.dossier")
    assert hasattr(dossier_module, "Dossier")
    assert hasattr(dossier_module, "Finding")
    assert inspect.getsource(dossier_module.Dossier).count("record_finding")


def test_gap_check_present():
    """Pass if orchestrator calls planner.revise_plan for gap checks."""
    orch = importlib.import_module("core.orchestrator")
    src = inspect.getsource(orch.run_pipeline)
    assert "revise_plan" in src


def test_dry_run_config_exists():
    """Pass if dry-run configuration exists."""
    assert Path("config/dry_run.yaml").exists()
