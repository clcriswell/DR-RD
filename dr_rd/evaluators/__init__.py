"""Built-in evaluators and registration."""

from extensions.registry import EvaluatorRegistry

from .compartment_check import evaluate as compartment_check
from .compliance import ComplianceEvaluator
from .cost import CostEvaluator
from .feasibility import FeasibilityEvaluator
from .novelty import NoveltyEvaluator
from .patent_overlap_check import evaluate as patent_overlap_check
from .reg_citation_check import evaluate as reg_citation_check
from .placeholder_check import evaluate as placeholder_check

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
    "reg_citation_check",
    "patent_overlap_check",
    "placeholder_check",
    "compartment_check",
    "feasibility_ev",
    "clarity_ev",
    "coherence_ev",
    "goal_fit_ev",
]
