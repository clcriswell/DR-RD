import json

import pytest

from utils import paths, run_config_io, run_reproduce


def test_load_and_map(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RUNS_ROOT", tmp_path)
    run_id = "r1"
    cfg = {
        "idea": "hi",
        "mode": "standard",
        "budget_limit_usd": 1.0,
        "max_tokens": 100,
        "knowledge_sources": ["web"],
        "advanced": {"foo": "bar"},
        "seed": 7,
    }
    lock = run_config_io.to_lockfile(cfg)
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "run_config.lock.json").write_text(json.dumps(lock))

    loaded = run_reproduce.load_run_inputs(run_id)
    kwargs = run_reproduce.to_orchestrator_kwargs(loaded)
    assert kwargs["idea"] == "hi"
    assert kwargs["knowledge_sources"] == ["web"]
    assert kwargs["foo"] == "bar"
    assert kwargs["seed"] == 7

    with pytest.raises(FileNotFoundError):
        run_reproduce.load_run_inputs("missing")
