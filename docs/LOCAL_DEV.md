# Local Development

This project can be run locally on macOS, Linux, or Windows. The steps below assume Python 3.9+.

## macOS/Linux

```bash
git clone https://github.com/clcriswell/DR-RD.git
cd DR-RD
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your keys
streamlit run app.py
```

## Windows (PowerShell)

```powershell
git clone https://github.com/clcriswell/DR-RD.git
cd DR-RD
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env  # add your keys
streamlit run app.py
```

## Docker

A simple development container is provided. Ensure `OPENAI_API_KEY` is set in your environment.

```bash
docker-compose up --build
```

## Troubleshooting

- **C++ build tools missing**: Some packages require a C++ compiler. On Windows install the [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
- **Port already in use**: Pass `--server.port` to `streamlit run app.py` to override the default port.
