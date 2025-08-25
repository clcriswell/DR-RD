# Migration Guide: Standard Profile Consolidation

## Summary
Single Standard profile replaces test/deep.

## What changed
- Removed mode branching; unified pipeline Planner → Router/Registry → Executor → Synthesizer.
- Model routing no longer depends on mode; test‑cheap fallback removed.
- UI no longer has “Mode: Test/Deep”; exposes RAG/Live‑Search toggles and numeric budget.

## Removed & Moved
- `orchestrators/router.py` → use `core.router`.
- `core/agents_registry.py` → use `core.agents.unified_registry.AGENT_REGISTRY`.
- `config/mode_profiles.py` removed; UI presets live in `app/ui_presets.py`.
- `evaluators/` package relocated to `dr_rd/evaluators/`.

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

## Retrieval & Search under Unified Pipeline
- **RAG on/off**: toggle `RAG_ENABLED=true|false`.
- **Live Search on/off**: toggle `ENABLE_LIVE_SEARCH=true|false`.
- Evaluators: controlled via `EVALUATORS_ENABLED`.
- Parallel execution: `PARALLEL_EXEC_ENABLED`.

## Checklist for integrators
- Remove any mode UI/CLI args.
- Use `apply_overrides()` for runtime toggles.
- RAG/Live‑Search toggles live in config/UI; no mode needed.
