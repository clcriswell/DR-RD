"""Built-in evaluators and registration."""
from dr_rd.extensions.registry import EvaluatorRegistry

from .cost import CostEvaluator
from .feasibility import FeasibilityEvaluator
from .novelty import NoveltyEvaluator
from .compliance import ComplianceEvaluator

# Register default evaluators
EvaluatorRegistry.register("cost", CostEvaluator)
EvaluatorRegistry.register("feasibility", FeasibilityEvaluator)
EvaluatorRegistry.register("novelty", NoveltyEvaluator)
EvaluatorRegistry.register("compliance", ComplianceEvaluator)


def _txt(x):
    try:
        return x if isinstance(x, str) else repr(x)
    except Exception:
        return ""


def _sig_score(text, signals):
    t = (text or "").lower()
    hits = sum(1 for s in signals if s and s.lower() in t)
    return min(1.0, 0.5 + 0.1 * hits)


def feasibility_ev(output, ctx):
    return _sig_score(_txt(output), ["feasible", "steps", "resources"])


def clarity_ev(output, ctx):
    return _sig_score(_txt(output), ["clear", "concise", "structured"])


def coherence_ev(output, ctx):
    return _sig_score(_txt(output), ["consistent", "no contradictions"])


def goal_fit_ev(output, ctx):
    return _sig_score(_txt(output), [str((ctx or {}).get("goal", ""))])


__all__ = [
    "CostEvaluator",
    "FeasibilityEvaluator",
    "NoveltyEvaluator",
    "ComplianceEvaluator",
    "feasibility_ev",
    "clarity_ev",
    "coherence_ev",
    "goal_fit_ev",
]
