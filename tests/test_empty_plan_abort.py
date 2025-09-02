from utils.paths import run_root

import core.orchestrator as orch


def test_empty_plan_aborts_before_executor(monkeypatch):
    monkeypatch.setattr(orch, "generate_plan", lambda *a, **k: [])
    events = list(orch.run_stream("idea", run_id="rid-empty", agents={}))
    assert any(e.kind == "error" for e in events)
    root = run_root("rid-empty")
    assert not (root / "build_spec.md").exists()
    assert not (root / "work_plan.md").exists()
