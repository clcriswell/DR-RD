from dr_rd.compliance import citation


def test_citation_validation():
    claims = [{"id": "c1", "text": "claim"}]
    sources = [{"id": "s1", "url": "https://federalregister.gov/doc/1"}]
    cits, cmap = citation.build_citation_graph(claims, sources)
    assert cmap["s1"] == "S1"
    res = citation.validate_citations(cits, ["federalregister.gov"], 0.5)
    assert res["coverage"] == 1.0
    assert res["ok"]
