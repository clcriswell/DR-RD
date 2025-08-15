import yaml, pathlib

def test_prices_yaml_schema():
    root = pathlib.Path(__file__).resolve().parents[1]
    prices = yaml.safe_load((root / "config" / "prices.yaml").read_text())
    assert "models" in prices and isinstance(prices["models"], dict)
    sample = next(iter(prices["models"].values()))
    assert "in_per_1k" in sample and "out_per_1k" in sample
