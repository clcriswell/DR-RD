from dataclasses import dataclass

# === Fill with your tenant’s actual prices ===
MODEL_PRICES = {
    "gpt-5":       {"in": 1.25/1000, "out": 10/1000},
    "gpt-5-mini":  {"in": 0.25/1000, "out":  2/1000},
    "gpt-5-nano":  {"in": 0.05/1000, "out":  0.40/1000},
    "o4-mini":     {"in": 0.20/1000, "out":  0.80/1000},   # TODO: update
    "o3":          {"in": 0.60/1000, "out":  2.40/1000},   # TODO: update
    "gpt-4o-mini": {"in": 0.15/1000, "out":  0.60/1000},
}

DEFAULTS = {
    "PLANNER":        "gpt-5-mini",
    "RESEARCHER":     "gpt-4o-mini",
    "EVALUATOR":      "gpt-4o-mini",
    "SYNTHESIZER":    "gpt-5-mini",
    "FINAL_SYNTH":    "gpt-5",
    "BRAIN_MODE_LOOP":"o4-mini",
}

@dataclass
class CallHints:
    stage: str                 # "plan"|"exec"|"eval"|"synth"|"brain"
    difficulty: str = "normal" # "easy"|"normal"|"hard"
    deep_reasoning: bool = False
    final_pass: bool = False
