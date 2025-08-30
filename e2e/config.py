import os

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8501")
APP_START_CMD = os.getenv(
    "APP_START_CMD",
    "streamlit run app.py --server.port 8501 --server.headless true",
)
APP_START_TIMEOUT_SEC = int(os.getenv("APP_START_TIMEOUT_SEC", "90"))
