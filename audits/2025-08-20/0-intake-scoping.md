# Intake & Scoping Audit

## Summary

Initial review of project intake and scoping components shows only partial support for orchestration.
Most intake, memory, and redaction controls are absent.


## Checklist
- [FAIL] 0.1 Streamlit intake screen capturing problem/goal, constraints, budget cap, time cap, allowed sources, redaction rules
- [PASS] 0.2 Orchestrator module present with entrypoint function and loop control
- [FAIL] 0.3 Memory layer with create/read/update and TTL or session keys
- [FAIL] 0.4 Config supports redaction and budget/time caps with enforcement
- [FAIL] 0.5 PII redaction utility with unit tests

## Evidence
- Orchestrator: `core/orchestrator.py`
- Memory manager without TTL: `memory/memory_manager.py`
- Budget config only: `config/modes.yaml`
- Ad-hoc query obfuscation: `utils/search_tools.py`

## Gaps
- No intake UI collecting required fields
- Memory lacks session scoping and expiration
- No configurable redaction rules or time caps
- No dedicated PII redaction utility or tests

## Minimal Fix Suggestions
- Add Streamlit intake form with required fields
- Extend memory layer with session keys and TTL
- Introduce config options for redaction, budget, and time caps; enforce them
- Implement PII redaction utility with corresponding tests
