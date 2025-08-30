import json
from utils import otel


def test_trace_id_from_run():
    tid = otel.trace_id_from_run("run123")
    assert len(tid) == 32
    int(tid, 16)


def test_configure_without_sdk(monkeypatch):
    monkeypatch.setattr(otel, "_trace", None)
    otel._tracer = None
    otel.configure()
    assert otel._tracer is None


def test_start_span_fallback_writes(tmp_path, monkeypatch):
    monkeypatch.setattr(otel, "_trace", None)
    otel._tracer = None
    monkeypatch.setattr(otel, "_FALLBACK_DIR", tmp_path)
    with otel.start_span("demo", attrs={"a": 1}, run_id="r1"):
        pass
    lines = (tmp_path / "spans.jsonl").read_text().strip().splitlines()
    assert lines
    rec = json.loads(lines[-1])
    assert rec["name"] == "demo"
    assert rec["attrs"]["a"] == 1
