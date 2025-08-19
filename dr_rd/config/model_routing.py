from dataclasses import dataclass

DEFAULTS = {
    "PLANNER": "o3-deep-research",
    "RESEARCHER": "o3-deep-research",
    "EVALUATOR": "o3-deep-research",
    "SYNTHESIZER": "o3-deep-research",
    "FINAL_SYNTH": "o3-deep-research",
    "BRAIN_MODE_LOOP": "o3-deep-research",
}


@dataclass
class CallHints:
    stage: str  # "plan"|"exec"|"eval"|"synth"|"brain"
    difficulty: str = "normal"  # "easy"|"normal"|"hard"
    deep_reasoning: bool = False
    final_pass: bool = False
