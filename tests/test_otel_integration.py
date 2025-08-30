import json
from types import SimpleNamespace
from utils import otel
import core.orchestrator as orch


def test_run_stream_writes_spans(tmp_path, monkeypatch):
    monkeypatch.setattr(otel, "_trace", None)
    otel._tracer = None
    monkeypatch.setattr(otel, "_FALLBACK_DIR", tmp_path)
    monkeypatch.setattr(orch.safety_utils, "check_text", lambda text: SimpleNamespace(findings=[]))
    monkeypatch.setattr(orch.trace_writer, "append_step", lambda *a, **k: None)
    monkeypatch.setattr(orch, "generate_plan", lambda *a, **k: [])
    monkeypatch.setattr(orch, "execute_plan", lambda *a, **k: {})
    monkeypatch.setattr(orch, "compose_final_proposal", lambda *a, **k: "ok")
    monkeypatch.setattr(orch.st, "session_state", {})
    list(orch.run_stream("idea", run_id="r123"))
    lines = (tmp_path / "spans.jsonl").read_text().strip().splitlines()
    records = [json.loads(l) for l in lines]
    assert any(r["name"] == "run" and r["attrs"].get("run_id") == "r123" for r in records)
