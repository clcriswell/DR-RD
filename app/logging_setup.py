import streamlit as st
import logging
from google.cloud import logging as gcp_logging
from google.oauth2 import service_account

def init_gcp_logging():
    # Load GCP service account from Streamlit secrets
    creds_info = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(creds_info)
    # Initialize Cloud Logging and attach to Python root logger
    client = gcp_logging.Client(credentials=credentials)
    client.setup_logging()
    logging.info("✅ Google Cloud Logging initialized")

# Run on import
init_gcp_logging()
