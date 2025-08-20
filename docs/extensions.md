# Extensions

This project supports registries for pluggable components. Each registry
maintains a simple mapping from a string name to a class.

## Example: Register an evaluator

```python
from extensions.abcs import BaseEvaluator
from extensions.registry import EvaluatorRegistry

class MyEval(BaseEvaluator):
    def evaluate(self, state: dict) -> dict:
        return {"score": 1.0}

EvaluatorRegistry.register("my_eval", MyEval)
```

Use ``EvaluatorRegistry.get("my_eval")`` to retrieve the class later.
