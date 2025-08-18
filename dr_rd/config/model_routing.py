from dataclasses import dataclass

DEFAULTS = {
    "PLANNER": "gpt-5-mini",
    "RESEARCHER": "gpt-4o-mini",
    "EVALUATOR": "gpt-4o-mini",
    "SYNTHESIZER": "gpt-5-mini",
    "FINAL_SYNTH": "gpt-4o",
    "BRAIN_MODE_LOOP": "o4-mini",
}


@dataclass
class CallHints:
    stage: str  # "plan"|"exec"|"eval"|"synth"|"brain"
    difficulty: str = "normal"  # "easy"|"normal"|"hard"
    deep_reasoning: bool = False
    final_pass: bool = False
