# AI R&D Center (Streamlit)

[![tests](https://github.com/clcriswell/DR-RD/actions/workflows/test.yml/badge.svg)](https://github.com/clcriswell/DR-RD/actions/workflows/test.yml)
[![secret-scan](https://github.com/clcriswell/DR-RD/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/clcriswell/DR-RD/actions/workflows/secret-scan.yml)

A public Streamlit application that masks a user’s idea, decomposes it into
multi-disciplinary research tasks, and orchestrates AI agents to synthesize a
prototype or development plan.

See the docs index in [docs/INDEX.md](docs/INDEX.md) for more information.

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
