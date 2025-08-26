from core.summarization.integrator import render_references


def test_citation_rendering():
    text = "Findings [S2] and [S1]."
    sources = [
        {"source_id": "S1", "title": "A", "url": "u1"},
        {"source_id": "S2", "title": "B", "url": "u2"},
        {"source_id": "S1", "title": "A", "url": "u1"},
    ]
    out = render_references(text, sources)
    assert "## References" in out
    assert out.strip().endswith("[S2] B (u2)")
