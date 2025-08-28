from dr_rd.rag import budget, types


def _hit(text, marker):
    doc = types.Doc(id="1", url=f"u{marker}", title="t", domain="gov", published_at=None, text=text, meta={"marker": marker})
    return types.Hit(doc=doc, score=1.0, components={})


def test_clip_respects_budget_and_cap():
    long_text = "sentence. " * 200
    hits = [_hit(long_text, "S1"), _hit(long_text, "S2")]
    bundle = budget.clip_to_budget(hits, token_budget=100, per_doc_token_cap=50)
    assert bundle.tokens_est <= 100
    for h in bundle.hits:
        assert len(h.doc.text) <= 50 * 4
