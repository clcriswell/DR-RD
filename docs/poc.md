# Proof-of-Concept Planning and Execution

This module enables deterministic simulation tests to validate an R&D hypothesis.

## Test Plan JSON
A `TestPlan` describes the project, hypothesis, and a set of test cases. Example:

```json
{
  "project_id": "demo-1",
  "hypothesis": "Cooling fin improves thermal performance by 15%.",
  "stop_on_fail": true,
  "tests": [
    {
      "id": "T1",
      "title": "Thermal drop at 50W",
      "inputs": {"power_w": 50, "ambient_c": 25, "_sim": "thermal_mock"},
      "metrics": [
        {"name": "delta_c", "operator": "<=", "target": 10.0, "unit": "C"},
        {"name": "safety_margin", "operator": ">=", "target": 0.2}
      ],
      "safety_notes": "no external calls"
    }
  ]
}
```

## Simulation Registry
Simulation functions register via `@register(name)` in `simulation.registry`. Each
function accepts an `inputs` dict and returns `(observations, meta)` where meta
contains `cost_estimate_usd` and `seconds`.

## Safety Gates
`core.poc.gates.assert_safe` ensures only registered simulations run. Tests that
reference unknown sims raise an exception.

## Sample Plan
The above JSON is used as a UI placeholder and can be edited to craft custom
Proof-of-Concept experiments.
