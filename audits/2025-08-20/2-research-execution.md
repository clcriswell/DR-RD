# Research Execution Audit

## Summary
- Reviewed multi-agent execution loop and surrounding infrastructure
- Identified missing dossier aggregation and dry-run configuration

## Checklist
- [PASS] 2.1 Agent loop controller present with pluggable role prompts
- [PASS] 2.2 External APIs abstracted behind adapters with token budgets
- [FAIL] 2.3 Dossier builder aggregates findings with source attribution
- [PASS] 2.4 Lead agent gap check implemented with retry or follow-up tasks
- [FAIL] 2.5 Runbook or config to enable dry-run with fixtures

## Evidence
- `core/orchestrator.py` – `run_pipeline` orchestrates iterative agent loop with `revise_plan`
- `core/llm_client.py` – `call_openai` wrapper integrates `BudgetManager`
- No module found matching `*dossier*` for source-attributed aggregation
- No runbook or config enabling dry-run with fixtures

## Gaps
- No dossier builder capturing findings with source attribution
- No documented dry-run configuration or runbook using fixtures

## Minimal fix suggestions
- Introduce a dossier aggregation module that records sources for each finding
- Provide a runbook or config flag to run the system against fixture data in dry-run mode
