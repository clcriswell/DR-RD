import os
import importlib
import glob


def test_streamlit_intake_screen_exists():
    """Fail if no Streamlit intake screen capturing required fields."""
    candidates = ["streamlit_app.py", "app.py"] + glob.glob("pages/*.py")
    found = False
    for path in candidates:
        if os.path.exists(path):

            needed = ["problem", "constraint", "budget", "time", "allowed", "redaction"]
            if all(term in text for term in needed):
                found = True
                break
    assert found, "Intake screen with required fields not found"


def test_orchestrator_module_present():
    orchestrator = importlib.import_module("core.orchestrator")
    assert hasattr(orchestrator, "orchestrate"), "Orchestrator entrypoint missing"


def test_memory_layer_has_ttl_or_session():
    path = "memory/memory_manager.py"
    assert os.path.exists(path), "Memory manager missing"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().lower()

    assert "ttl" in text or "session" in text, "Memory layer lacks TTL or session keys"


def test_config_supports_redaction_and_caps():
    path = "config/modes.yaml"
    assert os.path.exists(path), "modes.yaml missing"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().lower()

    assert "redact" in text and "time" in text, "Redaction or time caps not configured"


def test_pii_redaction_utility_has_tests():
    util_exists = os.path.exists("utils/redaction.py")
    test_exists = bool(glob.glob("tests/**/*redaction*.py"))
    assert util_exists and test_exists, "PII redaction utility or tests missing"
