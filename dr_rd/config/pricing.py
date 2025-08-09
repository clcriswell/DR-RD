PRICES = {
  "gpt-4o":      {"in": 0.005,  "out": 0.015},   # $ per 1K tokens (tune as needed)
  "gpt-4o-mini": {"in": 0.00015,"out": 0.00060},
  "gpt-5":       {"in": 0.010,  "out": 0.030}
}

def cost_usd(model: str, prompt_toks: int, completion_toks: int) -> float:
    p = PRICES.get(model, PRICES["gpt-4o"])
    return (prompt_toks/1000.0)*p["in"] + (completion_toks/1000.0)*p["out"]
