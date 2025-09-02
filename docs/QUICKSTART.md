# Quickstart

## Streamlit Community Cloud
1. Fork the repository.
2. In the Streamlit workspace, click **New app** and select the fork.
3. Under *Advanced settings*, add required secrets (`OPENAI_API_KEY`, optional `SERPAPI_KEY`).
4. Click **Deploy** and wait for the build to finish.

## Local Development
1. Install Python 3.10+ and Git.
2. Clone and set up a virtual environment:
   ```bash
   git clone https://github.com/clcriswell/DR-RD.git
   cd DR-RD
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Set API keys:
   ```bash
   export OPENAI_API_KEY=your_key
   export SERPAPI_KEY=optional_key
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```
