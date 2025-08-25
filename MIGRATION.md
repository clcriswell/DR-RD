# Migration Guide: Standard Profile Consolidation

## Summary
Single Standard profile replaces test/deep.

## What changed
- Removed mode branching; unified pipeline Planner → Router/Registry → Executor → Synthesizer.
- Model routing no longer depends on mode; test‑cheap fallback removed.
- UI no longer has “Mode: Test/Deep”; exposes RAG/Live‑Search toggles and numeric budget.

## Deprecated (supported one release with warnings)
- **DRRD_MODE** env var ("test"|"deep"|others) → ignored and mapped to standard.  
  Action: delete usage; pick behaviour via toggles and `modes.yaml`.
- **TEST_MODE** (in returned configs / session flags) → ignored by router/orchestrator; will be removed.  
  Action: do not branch on it.
- **TEST_MODEL_ID** → ignored by model router; will be removed.  
  Action: set stage/role models in config instead.
- **config.feature_flags.apply_mode_overrides** → alias to `apply_overrides`; will be removed.  
  Action: import/use `apply_overrides`.
- **DISABLE_IMAGES_BY_DEFAULT** map → superseded by single boolean `ENABLE_IMAGES`.

## How to achieve “cheap test” now
- Lower `target_cost_usd` in `config/modes.yaml`.
- Override stage/role models in config or via env (e.g., `DRRD_DEFAULT_MODEL` or updating `AGENT_MODEL_MAP`).

## Checklist for integrators
- Remove any mode UI/CLI args.
- Use `apply_overrides()` for runtime toggles.
- RAG/Live‑Search toggles live in config/UI; no mode needed.
