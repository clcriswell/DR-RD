import random

from core.llm import model_router
from core.llm.model_router import RouteContext, choose_model


def test_role_override_exec():
    ctx = RouteContext(role="Research Scientist", purpose="exec", size_hint=1000)
    decision = choose_model(ctx)
    assert decision.model == "claude-3-5-sonnet"


def test_ctx_filtering_prefers_backup():
    ctx = RouteContext(role=None, purpose="exec", size_hint=150000)
    decision = choose_model(ctx)
    assert decision.model == "gemini-1.5-pro"
    assert decision.reason == "no_preferred_ctx"


def test_gray_routing_probability(monkeypatch):
    ctx = RouteContext(role=None, purpose="exec", size_hint=1000)
    monkeypatch.setattr(random, "random", lambda: 0.01)
    decision = choose_model(ctx)
    assert decision.gray_probe is True
    monkeypatch.setattr(random, "random", lambda: 0.99)
    decision = choose_model(ctx)
    assert decision.gray_probe is False


def test_budget_downshift(monkeypatch):
    model_router._budgets_cfg = {"low": {"exec": {"max_tokens": 10}}}
    ctx = RouteContext(role="IP Analyst", purpose="exec", size_hint=1000, budget_profile="low")
    decision = choose_model(ctx)
    assert decision.model == "gpt-4.1-mini"
    assert decision.reason == "budget_downshift"
