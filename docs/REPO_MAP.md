# Repository Map

## Overview & Flow Diagram
User idea → Planner → Router/Registry → Executor → Synthesizer → UI

## Entry Points & Run Modes

### Entry Points
- streamlit_app: `app.py`
- package_init: `app/__init__.py:main`


### Runtime Modes
- **test**: target cost USD 2.5
- **deep**: target cost USD 2.5


## Agent Roster
| Role | Module | Contract |
| --- | --- | --- |
| HRM | `core/agents/hrm_agent.py` | JSON |
| Planner | `core/agents/planner_agent.py` | JSON |
| Reflection | `core/agents/reflection_agent.py` | JSON |
| ChiefScientist | `core/agents/chief_scientist_agent.py` | JSON |
| MaterialsEngineer | `core/agents/materials_engineer_agent.py` | JSON |
| RegulatorySpecialist | `core/agents/regulatory_specialist_agent.py` | JSON |


## Orchestrator & Executor Responsibilities
Contracts are strict JSON between pipeline stages.

## Config & Env Flags
Config files:
- `config/modes.yaml` (requires keys: test, deep)
- `config/prices.yaml` (requires keys: models)


Environment flags: DRRD_MODE, RAG_ENABLED, ENABLE_LIVE_SEARCH, SERPAPI_KEY

## What Runs When
Streamlit imports `app.main` from `app/__init__.py`.

## Change Rules & Conventions
See [REPO_RULES.md](REPO_RULES.md).

_Last generated at 2025-08-23T01:14:49.891377Z from commit 33feb6a_
