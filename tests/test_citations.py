from __future__ import annotations

from dr_rd.reporting.citations import bundle_citations, normalize_sources
from dr_rd.kb.models import KBSource


def test_marker_assignment_and_dedupe():
    s1 = KBSource(id="a", kind="web", url="http://x.com", title="X")
    s2 = KBSource(id="b", kind="web", url="http://x.com/", title="X")
    sections = [
        ("alpha {{a}} bravo", [s1]),
        ("charlie {{b}}", [s2]),
    ]
    processed, sources = bundle_citations(sections)
    assert "[S1]" in processed[0]
    assert "[S1]" in processed[1]
    assert len(sources) == 1
