import logging

from dr_rd.knowledge.bootstrap import bootstrap_vector_index


def test_vector_index_skip_flag(caplog):
    cfg = {
        "faiss_bootstrap_mode": "skip",
        "faiss_index_uri": "",
        "faiss_index_local_dir": ".faiss_index",
    }
    with caplog.at_level(logging.INFO):
        bootstrap_vector_index(cfg, logging.getLogger("test"))
    assert cfg["vector_index_present"] is False
    assert cfg["vector_index_source"] == "none"
    assert cfg.get("vector_doc_count") == 0
    logs = [r.message for r in caplog.records if "FAISSLoad" in r.message]
    assert len(logs) == 1
    assert "result=skip" in logs[0]
    assert "reason=bootstrap_skip" in logs[0]
