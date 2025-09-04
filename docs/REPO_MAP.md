# Repository Map

## Overview & Flow Diagram
User idea → Planner → Router/Registry → Executor → Summarization → Synthesizer → UI

## Entry Points & Run Modes

### Entry Points
- streamlit_app: `app.py`
- package_init: `app/__init__.py:main`


### Runtime Modes
- **standard**: target cost USD 2.5


## Agent Roster
| Role | Module | Contract |
| --- | --- | --- |
| CTO | `core/agents/cto_agent.py` | JSON |
| Research Scientist | `core/agents/research_scientist_agent.py` | JSON |
| Regulatory | `core/agents/regulatory_agent.py` | JSON |
| Finance | `core/agents/finance_agent.py` | JSON |
| Marketing Analyst | `core/agents/marketing_agent.py` | JSON |
| IP Analyst | `core/agents/ip_analyst_agent.py` | JSON |
| Planner | `core/agents/planner_agent.py` | JSON |
| Synthesizer | `core/agents/synthesizer_agent.py` | JSON |
| Mechanical Systems Lead | `core/agents/mechanical_systems_lead_agent.py` | JSON |
| HRM | `core/agents/hrm_agent.py` | JSON |
| Materials Engineer | `core/agents/materials_engineer_agent.py` | JSON |
| Reflection | `core/agents/reflection_agent.py` | JSON |
| Chief Scientist | `core/agents/chief_scientist_agent.py` | JSON |
| Regulatory Specialist | `core/agents/regulatory_specialist_agent.py` | JSON |
| Evaluation | `core/agents/evaluation_agent.py` | JSON |
| Materials | `core/agents/materials_agent.py` | JSON |
| QA | `core/agents/qa_agent.py` | JSON |
| Finance Specialist | `core/agents/finance_specialist_agent.py` | JSON |
| Simulation | `core/agents/simulation_agent.py` | JSON |
| Dynamic Specialist | `core/agents/dynamic_agent_wrapper.py` | JSON |


## Orchestrator & Executor Responsibilities
Contracts are strict JSON between pipeline stages.

## Config & Env Flags
Config files:
- `config/modes.yaml` (requires keys: standard)
- `config/prices.yaml` (requires keys: models)


Environment flags: DRRD_MODE (deprecated shim), RAG_ENABLED, ENABLE_LIVE_SEARCH, EVALUATORS_ENABLED, PARALLEL_EXEC_ENABLED, SERPAPI_KEY

## What Runs When
Streamlit imports `app.main` from `app/__init__.py`.

## Change Rules & Conventions
See [REPO_RULES.md](REPO_RULES.md).

_Last generated at 2025-09-04T16:31:19.018087Z from commit 450ddb1_
