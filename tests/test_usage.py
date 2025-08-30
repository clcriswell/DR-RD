import yaml

from utils import usage


def test_pricing_and_add_delta(tmp_path, monkeypatch):
    pricing = {"toy": {"input_per_1k": 1.0, "output_per_1k": 2.0}}
    p = tmp_path / "pricing.yaml"
    p.write_text(yaml.safe_dump(pricing), encoding="utf-8")
    monkeypatch.setattr(usage, "_PRICING_FILE", p)
    u = usage.Usage()
    u = usage.add_delta(u, model="toy", prompt_tokens=500, completion_tokens=500)
    assert u.cost_usd == 1.5  # 0.5*1 + 0.5*2
    u2 = usage.add_delta(usage.Usage(), model="toy", prompt_tokens=250, completion_tokens=250)
    merged = usage.merge(u, u2)
    assert merged.prompt_tokens == 750
    assert merged.completion_tokens == 750
    assert merged.total_tokens == 1500
    assert merged.cost_usd == 1.5 + 0.75


def test_thresholds():
    u = usage.Usage(prompt_tokens=0, completion_tokens=0, total_tokens=500, cost_usd=5.0)
    th = usage.thresholds(u, budget_limit_usd=10.0, token_limit=1000)
    assert th["budget_crossed"] is False
    assert th["budget_exceeded"] is False
    u2 = usage.Usage(prompt_tokens=0, completion_tokens=0, total_tokens=1000, cost_usd=10.0)
    th2 = usage.thresholds(u2, budget_limit_usd=10.0, token_limit=1000)
    assert th2["budget_crossed"] is True
    assert th2["budget_exceeded"] is True
