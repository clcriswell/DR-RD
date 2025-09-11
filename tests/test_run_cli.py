import json
from pathlib import Path

from scripts import run_cli


def test_run_cli_success(tmp_path, monkeypatch):
    def fake_generate(idea, **kwargs):
        import streamlit as st

        st.session_state["plan_tasks"] = ["t"]
        return []

    def fake_execute(idea, tasks, **kwargs):
        return {}

    def fake_compose(idea, answers, **kwargs):
        return "ok"

    monkeypatch.setattr("core.orchestrator.generate_plan", fake_generate)
    monkeypatch.setattr("core.orchestrator.execute_plan", fake_execute)
    monkeypatch.setattr("core.orchestrator.compose_final_proposal", fake_compose)

    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps({"idea": "x"}))
    out_dir = tmp_path / "runs"
    code = run_cli.main(["--config", str(cfg_path), "--out-dir", str(out_dir), "--no-telemetry"])
    assert code == 0
    run_dirs = list(out_dir.iterdir())
    assert run_dirs, "run directory created"
    rid_dir = run_dirs[0]
    assert (rid_dir / "run.json").exists()


def test_run_cli_error(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise Exception("boom")

    monkeypatch.setattr("core.orchestrator.generate_plan", boom)

    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps({"idea": "x"}))
    out_dir = tmp_path / "runs"
    code = run_cli.main(["--config", str(cfg_path), "--out-dir", str(out_dir), "--no-telemetry"])
    assert code == 1
