import os
import time
import yaml
import os
import time
import yaml
from memory.memory_manager import MemoryManager
from utils.redaction import load_policy, redact_text


def test_streamlit_intake_screen_exists():
    assert os.path.exists('streamlit_app.py') or os.path.isdir('app/pages'), 'Streamlit intake screen missing'


def test_orchestrator_module_has_run():
    from core.engine.cognitive_orchestrator import CognitiveOrchestrator
    assert callable(getattr(CognitiveOrchestrator, 'run', None))


def test_memory_manager_ttl(monkeypatch):
    mm = MemoryManager(ttl_default=1)
    mm.set('foo', 'bar', session_id='s')
    now = time.time()
    monkeypatch.setattr(time, 'time', lambda: now + 2)
    assert mm.get('foo', session_id='s') is None


def test_config_enforces_budget_and_time_caps():
    with open('config/modes.yaml', 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    mode = cfg.get('test', {})
    assert mode.get('enforce_caps') is True, 'Budget/time caps not enforced'
    assert mode.get('time_cap') is not None, 'Time cap missing'


def test_pii_redaction_utility():
    policy = load_policy('config/redaction.yaml')
    text = 'Email me at jane@example.com'
    result = redact_text(text, policy=policy)
    assert '[REDACTED:EMAIL]' in result
