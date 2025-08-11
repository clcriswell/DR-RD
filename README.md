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
