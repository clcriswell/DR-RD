from core.reporting.builder import build_report


def test_builder_renders_sections_and_redacts(tmp_path):
    state = {"summary": "Contact me at alice@example.com", "plan": "Do X", "meta": {"a": 1}}
    answers = {"Agent": "Finding"}
    sources = [{"title": "Src", "url": "http://example.com/secret"}]
    result = build_report(state, answers, sources, {"title": "My Report", "author": "Bob"})
    md = result["markdown"]
    assert "Executive Summary" in md
    assert "Plan & Tasks" in md
    assert "[S1]" in md
    # email redacted
    assert "[REDACTED:EMAIL]" in md
