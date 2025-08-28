from core.trace_models import Span
from dr_rd.safety.redaction_review import summarize_redactions, propose_overrides


def test_redaction_review():
    spans = [
        Span(id="1", parent_id=None, agent="a", tool="t", event=None,
             meta={"safety_meta": {"redactions_by_type": {"pii": 1}, "examples": {"pii": ["hash"]}}},
             t_start=1.0, t_end=2.0, duration_ms=100, ok=True)
    ]
    summary = summarize_redactions(spans)
    assert summary["counts_by_type"]["pii"] == 1
    assert summary["examples_by_type"]["pii"] == ["hash"]
    policies = {"benign": {"pii": "ignore example.com"}}
    overrides = propose_overrides(summary["counts_by_type"], policies)
    assert "ignore example.com" in overrides
