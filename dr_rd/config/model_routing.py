from dataclasses import dataclass

DEFAULTS = {
    "PLANNER": "gpt-5",
    "RESEARCHER": "gpt-5",
    "EVALUATOR": "gpt-5",
    "SYNTHESIZER": "gpt-5",
    "FINAL_SYNTH": "gpt-5",
    "BRAIN_MODE_LOOP": "gpt-5",
}


@dataclass
class CallHints:
    stage: str  # "plan"|"exec"|"eval"|"synth"|"brain"
    difficulty: str = "normal"  # "easy"|"normal"|"hard"
    deep_reasoning: bool = False
    final_pass: bool = False
