from __future__ import annotations

import subprocess


def test_thin_ui_guard() -> None:
    subprocess.run(["python", "scripts/check_thin_ui.py"], check=True)
