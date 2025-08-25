# Evaluation Extensions

The engine supports pluggable **evaluators** that score the workspace state
after each execution cycle. Evaluators implement the
`extensions.abcs.BaseEvaluator` interface:

```python
class BaseEvaluator(ABC):
    def evaluate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ...
```

The `evaluate` method should return a mapping with at least a `score` field
and an optional list of `notes`.

## Registering an evaluator

Create a module under `dr_rd/evaluators/` that subclasses `BaseEvaluator` and
registers it with the `EvaluatorRegistry`:

```python
from extensions.abcs import BaseEvaluator
from extensions.registry import EvaluatorRegistry

class MyEvaluator(BaseEvaluator):
    def evaluate(self, state: dict) -> dict:
        return {"score": 0.5, "notes": []}

EvaluatorRegistry.register("my_eval", MyEvaluator)
```

Once registered and `EVALUATORS_ENABLED` is set, the evaluator will be invoked
by the orchestrator and its score will contribute to the per‑cycle scorecard.

## Cost tracking

Evaluations run in both **deep** and **test** modes. Runs record token spend via a CostTracker for reporting only—no budget caps are enforced.
