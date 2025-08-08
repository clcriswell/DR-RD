from collections import defaultdict
from dr_rd.config.model_routing import MODEL_PRICES


class TokenMeter:
    def __init__(self):
        self.total_tokens = 0
        self.per_model = defaultdict(int)
        self.per_stage = defaultdict(int)

    def add_usage(self, model_id: str, stage: str, usage: dict):
        t = int(usage.get("total_tokens", 0) or 0)
        self.total_tokens += t
        self.per_model[model_id] += t
        self.per_stage[stage] += t

    def total(self):
        return self.total_tokens

    def by_model(self):
        return dict(self.per_model)

    def by_stage(self):
        return dict(self.per_stage)


def dollars_from_usage(model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
    p = MODEL_PRICES.get(model_id, {"in": 0.0, "out": 0.0})
    return (prompt_tokens / 1000.0) * p["in"] + (completion_tokens / 1000.0) * p["out"]
