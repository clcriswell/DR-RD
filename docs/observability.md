# Observability

This project captures additional observability artifacts during research execution.

## Evidence

Agent outputs can emit structured JSON blocks. These are parsed into `EvidenceItem`
records and persisted as `audits/<project_id>/evidence.json`.

## Coverage Map

For each agent role the text is scanned for evaluation dimensions such as
Feasibility, Novelty, Compliance and others. Results are written to
`audits/<project_id>/coverage.csv`.

## Decision Log

Major orchestration steps are appended to `memory/decision_log/<project_id>.jsonl`.
Each line records a timestamp, step name and payload.

## Enabling

The Streamlit UI exposes an **Observability** expander with checkboxes for:

- **Save decision log**
- **Save evidence & coverage**

Enable these to persist the above artifacts.
