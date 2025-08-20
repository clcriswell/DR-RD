# Research Execution Audit

## Summary
The repository includes an orchestrator that coordinates multiple agents and a dedicated LLM client adapter with token accounting. However, it lacks a dossier builder, a lead-agent gap check, and a runbook for dry-run execution.

## Checklist
- [PASS] 2.1 Agent loop controller present with pluggable role prompts
- [PASS] 2.2 External APIs abstracted behind adapters with time and token budgets
- [FAIL] 2.3 Dossier builder aggregates findings with source attribution
- [FAIL] 2.4 Lead agent gap check implemented with retry or follow-up tasks
- [FAIL] 2.5 Runbook or config to enable dry-run with fixtures

## Evidence
- `core/orchestrator.py` implements the agent loop controller.
- `core/llm_client.py` abstracts LLM calls and tracks token usage.

## Gaps
- No dossier builder for aggregating findings with sources.
- No lead-agent gap check to trigger follow-up tasks.
- No runbook or config to enable dry-run mode with fixtures.

## Minimal Fix Suggestions
- Introduce a dossier builder module that aggregates findings with citations.
- Implement a gap-check mechanism allowing lead agents to trigger retries or follow-up tasks.
- Provide a runbook or configuration enabling dry-run execution backed by fixtures.
