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

__all__ = [
    "CostEvaluator",
    "FeasibilityEvaluator",
    "NoveltyEvaluator",
    "ComplianceEvaluator",
]
