import os
import glob


def test_agent_loop_controller_exists():
    with open("core/orchestrator.py", "r", encoding="utf-8") as f:
        text = f.read()
    assert "run_pipeline" in text and "while True" in text, "Agent loop controller missing"


def test_external_api_adapter_with_budget():
    with open("core/llm_client.py", "r", encoding="utf-8") as f:
        text = f.read()
    assert "call_openai" in text and "BudgetManager" in text, "LLM adapter or budget tracking missing"


def test_dossier_builder_with_sources():
    assert glob.glob("core/*dossier*.py"), "Dossier builder missing"


def test_gap_check_followups():
    with open("core/orchestrator.py", "r", encoding="utf-8") as f:
        text = f.read()
    assert "revise_plan" in text, "Gap check or follow-up tasks missing"


def test_dry_run_runbook_or_config():
    assert os.path.exists("RUNBOOK.md"), "Dry-run runbook/config missing"
