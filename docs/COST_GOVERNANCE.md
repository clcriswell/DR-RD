# Cost & Budget Governance

Budgets are defined in `config/budgets.yaml` with profiles `low`, `standard`, and `high`.
Each profile contains caps for planning, routing, execution, and synthesis phases.

When `COST_GOVERNANCE_ENABLED` is true the router reads the active profile from
`feature_flags.BUDGET_PROFILE` and exposes applied caps in the `route_decision`
metadata block. Execution phase caps such as `max_tool_calls` and
`max_runtime_ms` are enforced by the tool router.
