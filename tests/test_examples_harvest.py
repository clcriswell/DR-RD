from __future__ import annotations

import time

from dr_rd.examples import harvest, catalog, bridge_registry
from dr_rd.kb.models import KBRecord, KBSource


def test_harvest_and_catalog(tmp_path, monkeypatch):
    # prepare kb records
    recs = [
        KBRecord(
            id="1",
            run_id="r1",
            agent_role="X",
            task_title="t",
            task_desc="d",
            inputs={},
            output_json={"o": 1},
            sources=[KBSource(id="s1", kind="web")],
            ts=time.time(),
            metrics={"quality_score": 0.9},
        ),
        KBRecord(
            id="2",
            run_id="r1",
            agent_role="X",
            task_title="t2",
            task_desc="d",
            inputs={},
            output_json={},
            sources=[],
            ts=time.time(),
            metrics={"quality_score": 0.9},
        ),
    ]
    examples = harvest(recs)
    assert len(examples) == 1
    # catalog refresh and fetch
    monkeypatch.setattr(catalog, "EXAMPLE_DIR", tmp_path / "examples")
    monkeypatch.setattr(bridge_registry.catalog, "EXAMPLE_DIR", tmp_path / "examples")
    catalog.EXAMPLE_DIR.mkdir(exist_ok=True)
    catalog.refresh(examples)
    fetched = bridge_registry.get_examples("X", n=1)
    assert fetched and fetched[0]["role"] == "X"
