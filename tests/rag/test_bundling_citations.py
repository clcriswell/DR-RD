from dr_rd.rag import bundling, types


def test_bundle_stable_markers():
    hits = [
        types.Hit(doc=types.Doc(id="1", url="u1", title="t1", domain="gov", published_at=None, text="a", meta={}), score=1.0),
        types.Hit(doc=types.Doc(id="2", url="u2", title="t2", domain="gov", published_at=None, text="b", meta={}), score=0.9),
        types.Hit(doc=types.Doc(id="3", url="u1", title="t1", domain="gov", published_at=None, text="a", meta={}), score=0.8),
    ]
    marked, sources, mmap = bundling.bundle_citations(hits)
    assert [s["id"] for s in sources] == ["S1", "S2"]
    assert marked[0].doc.meta["marker"] == "S1"
    assert marked[2].doc.meta["marker"] == "S1"
