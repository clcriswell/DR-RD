import json
from scripts import batch_run


def test_batch_run(tmp_path, monkeypatch):
    def fake_generate(idea, **kwargs):
        if idea == "timeout":
            raise TimeoutError("deadline reached")
        return []

    def fake_execute(idea, tasks, **kwargs):
        return {}

    def fake_compose(idea, answers, **kwargs):
        return "ok"

    monkeypatch.setattr("core.orchestrator.generate_plan", fake_generate)
    monkeypatch.setattr("core.orchestrator.execute_plan", fake_execute)
    monkeypatch.setattr("core.orchestrator.compose_final_proposal", fake_compose)

    jsonl_path = tmp_path / "items.jsonl"
    jsonl_path.write_text("\n".join([
        json.dumps({"idea": "ok", "mode": "demo"}),
        json.dumps({"idea": "timeout", "mode": "demo"}),
    ]))
    out_dir = tmp_path / "runs"
    monkeypatch.chdir(tmp_path)
    code = batch_run.main([
        "--jsonl", str(jsonl_path),
        "--concurrency", "2",
        "--out-dir", str(out_dir),
        "--no-telemetry",
    ])
    assert code == 2
    summary = json.loads((tmp_path / "batch_summary.json").read_text())
    assert summary["counts"]["success"] == 1
    assert summary["counts"]["timeout"] == 1
    assert len(summary["runs"]) == 2
