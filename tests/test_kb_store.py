from __future__ import annotations

import time

from dr_rd.kb import store
from dr_rd.kb.models import KBRecord, KBSource


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(store, "CFG_DIR", tmp_path)
    monkeypatch.setattr(store, "STORE_PATH", tmp_path / "kb.jsonl")
    monkeypatch.setattr(store, "INDEX_PATH", tmp_path / "kb_index.jsonl")


def test_add_get_query_compact(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    rec = KBRecord(
        id="1",
        run_id="r1",
        agent_role="A",
        task_title="t",
        task_desc="d",
        inputs={},
        output_json={},
        sources=[KBSource(id="s1", kind="web", url="http://a", title="A")],
        ts=time.time(),
    )
    store.add(rec)
    assert store.get("1").agent_role == "A"
    assert store.query({"agent_role": "A"})
    # duplicate id
    store.add(rec)
    store.compact()
    records = store.query({}, limit=0)
    assert len(records) == 1
