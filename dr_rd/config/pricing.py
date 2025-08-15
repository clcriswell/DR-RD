PRICES = {
    "gpt-4o": {"in": 0.00500, "out": 0.02000},
    "gpt-4o-mini": {"in": 0.00060, "out": 0.00240},
    "gpt-5": {"in": 0.00125, "out": 0.01000},
}


def cost_usd(model: str, prompt_toks: int, completion_toks: int) -> float:
    p = PRICES.get(model, PRICES["gpt-4o"])
    return (prompt_toks / 1000.0) * p["in"] + (completion_toks / 1000.0) * p["out"]
