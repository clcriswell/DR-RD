import math
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Reservation:
    stage: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float


class BudgetManager:
    """Track spend against a target dollar budget for a run."""

    def __init__(self, mode_cfg: Dict, price_table: Dict, safety_margin: float = 0.05):
        self.target_cost_usd: float = float(mode_cfg.get("target_cost_usd", 0.0))
        self.price_table: Dict = price_table or {"models": {}}
        self.stage_weights: Dict[str, float] = mode_cfg.get("stage_weights", {})
        self.safety_margin: float = safety_margin
        self.reset_run()

    # ------------------------------------------------------------------
    def reset_run(self) -> None:
        self.spend: float = 0.0
        self.stage_spend: Dict[str, float] = {s: 0.0 for s in self.stage_weights}

    # ------------------------------------------------------------------
    def _price(self, model_id: str) -> Dict[str, float]:
        models = self.price_table.get("models", {})
        return models.get(model_id, models.get("default", {"in_per_1k": 0.0, "out_per_1k": 0.0}))

    def cost_of(self, model_id: str, prompt_tokens: int, completion_tokens: int) -> float:
        p = self._price(model_id)
        return (prompt_tokens / 1000.0) * p.get("in_per_1k", 0.0) + (
            completion_tokens / 1000.0
        ) * p.get("out_per_1k", 0.0)

    # ------------------------------------------------------------------
    def remaining_usd(self) -> float:
        cap = self.target_cost_usd * (1.0 - self.safety_margin)
        return max(0.0, cap - self.spend)

    def _remaining_stage_usd(self, stage: str) -> float:
        if not self.stage_weights:
            return self.remaining_usd()
        cap = self.target_cost_usd * self.stage_weights.get(stage, 0)
        return max(0.0, cap - self.stage_spend.get(stage, 0.0))

    def remaining_tokens(self, model_id: str, direction: str = "prompt") -> int:
        price = self._price(model_id)
        rate = price.get("in_per_1k" if direction == "prompt" else "out_per_1k", 0.0)
        if rate <= 0:
            return math.inf
        return int(self.remaining_usd() / rate * 1000)

    # ------------------------------------------------------------------
    def can_afford(
        self,
        next_stage_name: str,
        model_id: str,
        est_prompt_tokens: int,
        est_completion_tokens: int,
    ) -> bool:
        cost = self.cost_of(model_id, est_prompt_tokens, est_completion_tokens)
        return cost <= self.remaining_usd() and cost <= self._remaining_stage_usd(next_stage_name)

    def reserve(
        self,
        next_stage_name: str,
        model_id: str,
        est_prompt_tokens: int,
        est_completion_tokens: int,
    ) -> Reservation:
        cost = self.cost_of(model_id, est_prompt_tokens, est_completion_tokens)
        self.stage_spend[next_stage_name] = self.stage_spend.get(next_stage_name, 0.0) + cost
        self.spend += cost
        return Reservation(next_stage_name, model_id, est_prompt_tokens, est_completion_tokens, cost)

    def consume(
        self,
        actual_prompt_tokens: int,
        actual_completion_tokens: int,
        model_id: str,
        stage: Optional[str] = None,
    ) -> float:
        cost = self.cost_of(model_id, actual_prompt_tokens, actual_completion_tokens)
        self.spend += cost
        if stage:
            self.stage_spend[stage] = self.stage_spend.get(stage, 0.0) + cost
        return cost
