import logging

from dr_rd.core.config_snapshot import build_resolved_config_snapshot
from dr_rd.knowledge.bootstrap import bootstrap_vector_index


def test_bootstrap_skip_flags(tmp_path):
    cfg = {
        "faiss_bootstrap_mode": "skip",
        "faiss_index_local_dir": tmp_path / "idx",
    }
    res = bootstrap_vector_index(cfg, logging.getLogger(__name__))
    assert res["present"] is False
    cfg["vector_index_present"] = res["present"]
    cfg["vector_doc_count"] = res["doc_count"]
    snap = build_resolved_config_snapshot(cfg)
    assert snap["vector_index_present"] is False
    assert snap["vector_doc_count"] == 0
