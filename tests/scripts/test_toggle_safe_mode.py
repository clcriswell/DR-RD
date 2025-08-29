import subprocess
import sys
from pathlib import Path


def test_toggle_safe_mode(tmp_path):
    env_file = tmp_path / ".env.flags"
    script = Path("scripts/toggle_safe_mode.py")
    subprocess.check_call([sys.executable, str(script), "--path", str(env_file)])
    first = env_file.read_text().strip().splitlines()
    subprocess.check_call([sys.executable, str(script), "--path", str(env_file)])
    second = env_file.read_text().strip().splitlines()
    assert set(first) == set(second)
    assert any(line == "RAG_ENABLED=0" for line in first)
