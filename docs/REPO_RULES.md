# Repository Rules

## Single Source of Truth
- `repo_map.yaml` and `docs/REPO_MAP.md` describe how the system is wired. Regenerate them with `make repo-map` whenever components move or change.
- Avoid duplicating modules. UI code in `app.py` stays thin, while business logic lives in orchestrators under `orchestrators/`.

## Adding an Agent
1. Place the agent implementation in `core/agents/`.
2. Register the role in `core/agents/unified_registry.py`.
3. Provide prompts/contracts and add tests in `tests/`.
4. Run `make repo-map` and commit the updated map and docs.

## Configuration Changes
- Only modify `config/modes.yaml` or `config/prices.yaml` when changing budgets or model pricing.
- After editing, regenerate the map with `make repo-map`.

## File Naming & Placement
- Agents: `core/agents/<role>_agent.py`
- Prompts: `prompts/`
- Orchestrators: `orchestrators/`
- Tests: `tests/`
- Docs: `docs/`

## Pull Request Checklist
- `make repo-map` run and changes committed.
- New or changed agent includes registry update and tests.
- Config updates accompanied by regenerated map.
- Verified no duplicate modules or conflicting responsibilities.
