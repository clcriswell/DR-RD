from core.trace.filters import apply_filters, group_stats
from core.trace.schema import TraceBundle, TraceEvent


def _sample_bundle() -> TraceBundle:
    events = [
        TraceEvent(ts=1, node="n1", phase="exec", task_id="t1", agent="a1", tool="tool1", attempt=1, duration_s=2, tokens=10, cost_usd=0.1),
        TraceEvent(ts=2, node="n2", phase="exec", task_id="t2", agent="a2", tool="tool2", attempt=2, duration_s=1, tokens=5, cost_usd=0.05),
    ]
    return TraceBundle(events=events)


def test_apply_filters_and_retries():
    bundle = _sample_bundle()
    f = apply_filters(bundle, by_agent=["a1"])
    assert len(f.events) == 1 and f.events[0].agent == "a1"
    r = apply_filters(bundle, retries_only=True)
    assert len(r.events) == 1 and r.events[0].attempt == 2


def test_group_stats_totals():
    bundle = _sample_bundle()
    stats = group_stats(bundle, "agent")
    assert stats["a1"]["tokens"] == 10
    assert stats["a2"]["count"] == 1
