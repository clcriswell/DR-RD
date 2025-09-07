from __future__ import annotations

from scripts import demo_specialists


def test_demo_script_runs(monkeypatch):
    calls = [
        {"role": "Materials Engineer"},
        {"role": "QA"},
        {"role": "Finance"},
        {"role": "Materials Engineer"},
    ]

    def fake_run(role, title, desc, inputs, flag_overrides):
        return calls.pop(0)

    monkeypatch.setattr("scripts.demo_specialists.ui_bridge.run_specialist", fake_run)
    results = demo_specialists.run_demo()
    assert isinstance(results, list) and len(results) == 3
