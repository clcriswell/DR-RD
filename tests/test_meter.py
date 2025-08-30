from types import SimpleNamespace

from utils.usage import Usage
from app.ui import meter


class DummyProgress:
    def __init__(self):
        self.last = None

    def progress(self, value):
        self.last = value

    def update(self, value):
        self.last = value


def _fake_st():
    return SimpleNamespace(
        progress=lambda v=0: DummyProgress(),
        metric=lambda *a, **k: None,
        caption=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        columns=lambda n: [SimpleNamespace(progress=lambda v=0: DummyProgress(), metric=lambda *a, **k: None, caption=lambda *a, **k: None, warning=lambda *a, **k: None) for _ in range(n)],
    )


def test_render_live_no_limits(monkeypatch):
    st = _fake_st()
    monkeypatch.setattr(meter, "st", st)
    meter.render_live(Usage(), budget_limit_usd=None, token_limit=None)


def test_render_live_with_limits(monkeypatch):
    st = _fake_st()
    monkeypatch.setattr(meter, "st", st)
    meter.render_live(Usage(cost_usd=1.0, total_tokens=100), budget_limit_usd=10.0, token_limit=1000)


def test_render_summary(monkeypatch):
    st = _fake_st()
    monkeypatch.setattr(meter, "st", st)
    meter.render_summary(Usage(cost_usd=2.0, total_tokens=200))
