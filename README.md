# AI R&D Center (Streamlit)

A public Streamlit application that masks a user’s idea, decomposes it into
multi-disciplinary research tasks, and orchestrates AI agents to synthesize a
prototype or development plan.

_Current repo state_  
**Step 1:** Minimal Streamlit front-end + “Creation Planner” prompt.

## Quick start (local)

```bash
git clone https://github.com/YOUR_USERNAME/rnd_tool.git
cd rnd_tool
python -m venv .venv && source .venv/bin/activate   # PowerShell: .venv\Scripts\activate
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
streamlit run app.py
