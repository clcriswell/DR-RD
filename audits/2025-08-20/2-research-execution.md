# Research Execution Audit

## Summary
The agent loop controller and API adapter exist with budget tracking, but dossier aggregation and dry-run guidance are missing.

## Checklist
- [PASS] 2.1 Agent loop controller present with pluggable role prompts
- [PASS] 2.2 External APIs abstracted behind adapters with time and token budgets
- [FAIL] 2.3 Dossier builder aggregates findings with source attribution
- [PASS] 2.4 Lead agent gap check implemented with retry or follow-up tasks
- [FAIL] 2.5 Runbook or config to enable dry-run with fixtures

## Evidence
- Agent loop: `core/orchestrator.py::run_pipeline`
- LLM adapter with budgets: `core/llm_client.py`
- Gap check via planner revision: `core/orchestrator.py` ("revise_plan" call)
- Failing tests:
  - `tests/audit/test_research_execution.py::test_dossier_builder_present`
  - `tests/audit/test_research_execution.py::test_dry_run_runbook_exists`

## Gaps
- No module dedicated to dossier aggregation with source attribution
- No documented dry-run runbook or configuration

## Minimal Fix Suggestions
- Add dossier builder that compiles findings with source links
- Provide runbook or configuration flag for dry-run execution
