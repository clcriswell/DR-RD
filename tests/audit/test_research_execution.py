import os
import glob
import importlib


def test_agent_loop_controller_present():
    orchestrator = importlib.import_module("core.orchestrator")
    assert hasattr(orchestrator, "orchestrate"), "Agent loop controller missing"


def test_external_api_adapter_has_budgets():
    path = "core/llm_client.py"
    assert os.path.exists(path), "LLM client adapter missing"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().lower()
    assert "token" in text or "budget" in text, "API adapter lacks token or budget tracking"


def test_dossier_builder_exists():
    candidates = glob.glob("**/*dossier*.py", recursive=True)
    assert candidates, "Dossier builder missing"


def test_lead_agent_gap_check_present():
    orchestrator = importlib.import_module("core.orchestrator")
    assert hasattr(orchestrator, "gap_check"), "Lead agent gap check not implemented"


def test_dry_run_runbook_present():
    assert os.path.exists("RUNBOOK.md"), "Dry-run runbook missing"
