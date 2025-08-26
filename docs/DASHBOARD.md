# Multi Project Dashboard

The dashboard aggregates metrics across projects. Data can come from Firestore
or an in-memory store. Logic lives in `core/dashboard/aggregate.py`.

## Project Discovery
`list_projects` enumerates available projects. When Firestore is unavailable the
UI falls back to session memory. The number of projects is capped by
`DASHBOARD_MAX_PROJECTS`.

## Metrics
`collect_project_metrics` rolls up run information:
- last run timestamp
- task count
- average evaluator score (if available)
- tool and retrieval calls
- total cost (USD)
- wall time

## Comparisons and Exports
`compare_projects` normalises metrics for side-by-side comparisons. A maximum of
`DASHBOARD_MAX_COMPARE` projects can be compared at once.

The dashboard can export CSV/JSON rollups and a PDF snapshot using the reporting
PDF helper.
