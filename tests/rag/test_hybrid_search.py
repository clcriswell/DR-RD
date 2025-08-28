from dr_rd.rag import types, hybrid, retrievers

class StubBM25(retrievers.Retriever):
    name = "bm25"
    def search(self, spec):
        doc1 = types.Doc(id="1", url="u1", title="t1", domain="gov", published_at=None, text="alpha", meta={"score":2})
        doc2 = types.Doc(id="2", url="u2", title="t2", domain="blog", published_at=None, text="beta", meta={"score":1})
        return [doc1, doc2]

class StubDense(retrievers.Retriever):
    name = "dense"
    def search(self, spec):
        doc1 = types.Doc(id="1", url="u1", title="t1", domain="gov", published_at=None, text="alpha", meta={"score":1})
        doc3 = types.Doc(id="3", url="u3", title="t3", domain="edu", published_at=None, text="gamma", meta={"score":3})
        return [doc1, doc3]


def test_hybrid_fusion_dedupe():
    spec = types.QuerySpec(role="r", task="t", query="alpha", top_k=5, policy="LIGHT")
    hits = hybrid.hybrid_search(spec, [StubBM25(), StubDense()])
    urls = [h.doc.url for h in hits]
    assert urls.count("u1") == 1  # dedup
    assert hits[0].score >= hits[1].score
    assert "bm25" in hits[0].components and "dense" in hits[0].components
