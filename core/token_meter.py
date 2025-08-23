from collections import defaultdict


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


def dollars_from_usage(
    model_id: str, prompt_tokens: int, completion_tokens: int
) -> float:
    from app.price_loader import cost_usd

    return cost_usd(model_id, prompt_tokens, completion_tokens)
