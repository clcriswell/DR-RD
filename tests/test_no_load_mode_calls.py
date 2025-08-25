import subprocess
from pathlib import Path


def test_no_load_mode_calls():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["rg", "load_mode", "-l", "-g", "*.py"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    files = [
        f for f in result.stdout.splitlines() if f != "app/config_loader.py" and f.endswith(".py")
    ]
    assert not files, f"load_mode references remain: {files}"
