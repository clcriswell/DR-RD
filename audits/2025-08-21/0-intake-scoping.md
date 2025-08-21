# Area 0: Intake & Scoping

## Summary
Initial check for intake mechanisms, orchestration, memory, and redaction.

## Checklist
- [ ] 0.1 Streamlit intake screen exists capturing required fields — FAIL
- [x] 0.2 Orchestrator module with loop control — PASS
- [x] 0.3 Memory layer with TTL/session keys — PASS
- [ ] 0.4 Config supports redaction and budget/time caps with enforcement — FAIL
- [x] 0.5 PII redaction utility with unit tests — PASS

## Evidence
- 0.2 `core/engine/cognitive_orchestrator.py` exposes `CognitiveOrchestrator.run()`【F:core/engine/cognitive_orchestrator.py†L27-L44】 【F:core/engine/cognitive_orchestrator.py†L146-L155】
- 0.3 `memory/memory_manager.py` implements TTL-based `set`/`get` with session IDs【F:memory/memory_manager.py†L21-L55】
- 0.4 `config/modes.yaml` sets `enforce_caps: false` and lacks time caps【F:config/modes.yaml†L1-L10】
- 0.5 `utils/redaction.py` with patterns and `tests/utils/test_redaction.py` unit tests【F:utils/redaction.py†L1-L30】【F:tests/utils/test_redaction.py†L1-L15】
- Missing Streamlit intake screen (no `streamlit_app.py` or pages)【13c654†L1-L2】

## Gaps
- No intake UI to collect problem statement, constraints, budgets, time limits, allowed sources, or redaction rules.
- Budget enforcement disabled and time caps missing from config.

## Minimal Fix Suggestions
- Add `streamlit_app.py` with fields for problem, constraints, budget cap, time cap, allowed sources, and redaction rules.
- Introduce time cap settings in config and enforce `enforce_caps` in runtime code.
