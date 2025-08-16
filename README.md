# AI R&D Center (Streamlit)

A public Streamlit application that masks a user’s idea, decomposes it into
multi-disciplinary research tasks, and orchestrates AI agents to synthesize a
prototype or development plan.

_Current repo state_  
**Step 1:** Minimal Streamlit front-end + “Creation Planner” prompt.

The planner now uses OpenAI's JSON mode for reliable parsing.

## Quick start (local)

```bash
git clone https://github.com/YOUR_USERNAME/rnd_tool.git
cd rnd_tool
python -m venv .venv && source .venv/bin/activate   # PowerShell: .venv\Scripts\activate
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
streamlit run app.py
```

## Multi-agent execution

DR-RD now performs a three stage pipeline:

1. **Planner** decomposes your idea into specialist tasks.
2. Each task is routed to a matching agent (CTO, Research, Regulatory or Finance) which replies using a JSON contract:

```json
{"role": "...", "task": "...", "findings": [], "risks": [], "next_steps": []}
```

3. A synthesizer combines the findings into a unified plan.

Model selections and **budget caps** for different modes live in `config/modes.yaml`.
Each mode specifies a `target_cost_usd`, default models for the planning/execution/synthesis stages,
and limits such as `k_search` and `max_loops`.

Token pricing lives in `config/prices.yaml` (override via `PRICES_PATH`).

Set the mode via `DRRD_MODE` or the Streamlit dropdown. The Streamlit interface now includes an **Agent Trace** expander showing which agent handled each task, token counts and a brief finding.

### Modes & Cost

| Mode     | Plan model | Exec model  | Synth model | max_loops | Notes |
|----------|------------|-------------|-------------|-----------|-------|
| Test     | 4o         | 4o-mini     | 4o          | 1         | images disabled |
| Balanced | 4o         | 4o-mini     | 4o          | 2         | images disabled |
| Deep     | 4o         | 4o-mini     | gpt-5       | 1         | images enabled |

Images are disabled by default for the Test and Balanced modes.

## Quick Start
1) `pip install -r requirements.txt`
2) Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
3) `streamlit run app.py`
4) (Optional) Build a RAG index: `python scripts/build_faiss_index.py`
   Then enable `RAG_ENABLED=true` in your environment.

### Run profiles

- **Lite**: deterministic single-pass pipeline with a hard budget cap. Good for demos and CI smoke tests.
- **Pro**: full HRM engine with planning, evaluators, optional RAG, simulations, and persistence.

Select the profile in the sidebar. To default to Lite when launching programmatically:

```bash
DRRD_DEFAULT_PROFILE=Lite streamlit run app.py
```
