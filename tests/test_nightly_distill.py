from __future__ import annotations

import json
import time

from dr_rd.kb import store, index
from dr_rd.examples import catalog
from dr_rd.kb.models import KBRecord, KBSource


def test_distill_script(monkeypatch, tmp_path):
    # setup temporary kb
    monkeypatch.setattr(store, "CFG_DIR", tmp_path)
    monkeypatch.setattr(store, "STORE_PATH", tmp_path / "kb.jsonl")
    monkeypatch.setattr(store, "INDEX_PATH", tmp_path / "kb_index.jsonl")
    monkeypatch.setattr(index, "INDEX_FILE", tmp_path / "kb_index.jsonl")
    monkeypatch.setattr(catalog, "EXAMPLE_DIR", tmp_path / "examples")
    catalog.EXAMPLE_DIR.mkdir(exist_ok=True)
    rec = KBRecord(
        id="1",
        run_id="r1",
        agent_role="A",
        task_title="t",
        task_desc="d",
        inputs={},
        output_json={},
        sources=[KBSource(id="s1", kind="web")],
        ts=time.time(),
    )
    store.add(rec)
    monkeypatch.chdir(tmp_path)
    import scripts.nightly_distill as nd

    nd.main()
    assert (tmp_path / "distill_report.md").exists()
