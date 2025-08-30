from utils.eval import runner
from utils.stream_events import Event


def fake_run_stream(idea, run_id, agents):
    yield Event("summary", phase="synth", text="foo")
    yield Event("usage_delta", meta={"prompt_tokens": 1, "completion_tokens": 1, "cost_usd": 0.01})
    yield Event("done")


def test_run_eval_writes_results(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "run_stream", fake_run_stream)
    monkeypatch.setattr(runner, "get_agents", lambda: {})
    items = [{"id": "t1", "idea": "hi", "expected_keywords": ["foo"], "limits": {}}]
    summary = runner.run_eval(items, out_dir=str(tmp_path))
    assert (tmp_path / "results" / "t1.json").exists()
    assert summary["pass_rate"] == 1.0
