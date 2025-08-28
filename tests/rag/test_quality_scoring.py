from datetime import datetime, timedelta, timezone

from dr_rd.rag import quality, types


def test_domain_recency_scoring_order():
    recent = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    old = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
    doc1 = types.Doc(id="1", url="u1", title="t1", domain="gov", published_at=recent, text="alpha beta", meta={})
    doc2 = types.Doc(id="2", url="u2", title="t2", domain="blog", published_at=old, text="alpha", meta={})
    q = "alpha"
    s1 = quality.score_source(doc1, q)
    s2 = quality.score_source(doc2, q)
    assert s1 > s2
