from dr_rd.rag import types
from core import retrieval
import config.feature_flags as ff
from dr_rd.rag import hybrid


def test_blocked_domain_retry(monkeypatch):
    ff.EVALUATORS_ENABLED = True
    bad_doc = types.Doc(id="b", url="https://bad.com/x", title="b", domain="bad", published_at=None, text="bad", meta={"score":1})
    bad_hit = types.Hit(doc=bad_doc, score=1.0)
    def fake(spec, retrievers_list):
        return [bad_hit]
    monkeypatch.setattr(hybrid, "hybrid_search", fake)
    bundle = retrieval.run_retrieval("r", "t", "bad", {"policy":"LIGHT","top_k":1}, {})
    assert all("bad.com" not in s["url"] for s in bundle.sources)
    assert bundle.hits
