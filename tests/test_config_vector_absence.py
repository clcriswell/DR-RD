import logging

from dr_rd.knowledge.bootstrap import bootstrap_vector_index
from dr_rd.core.config_snapshot import build_resolved_config_snapshot


def test_vector_absent_snapshot(tmp_path):
    cfg = {
        "faiss_bootstrap_mode": "skip",
        "faiss_index_local_dir": tmp_path / "idx",
    }
    bootstrap_vector_index(cfg, logging.getLogger(__name__))
    snap = build_resolved_config_snapshot(cfg)
    assert snap["vector_index_present"] is False
    assert snap.get("vector_doc_count", 0) == 0
    assert snap.get("vector_index_source") == "none"
