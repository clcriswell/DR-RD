"""Share links page."""

from __future__ import annotations

import streamlit as st

from dr_rd.config.env import get_env
from utils.prefs import load_prefs
from utils.share_links import make_link
from utils.telemetry import share_link_created

st.title("Share run")

prefs = load_prefs().get("sharing", {})
allow_scopes = prefs.get("allow_scopes", ["trace", "reports", "artifacts"])
default_scopes = prefs.get("default_scopes", allow_scopes)
default_ttl = int(prefs.get("default_ttl_sec", 604800))

run_id = st.text_input("Run ID", st.query_params.get("run_id", ""))
scopes = st.multiselect("Scopes", options=allow_scopes, default=default_scopes)
opt = st.selectbox("TTL", ["24h", "7d", "30d", "Custom"], index=1)
if opt == "24h":
    ttl = 24 * 3600
elif opt == "7d":
    ttl = 7 * 86400
elif opt == "30d":
    ttl = 30 * 86400
else:
    ttl = int(st.number_input("TTL seconds", min_value=60, value=default_ttl))

if st.button("Create link", disabled=not run_id or not scopes):
    base = get_env("APP_BASE_URL", ".").rstrip("/")
    link = make_link(base, run_id, scopes=scopes, ttl_sec=ttl)
    st.text_input("Share link", value=link, help="Copy this link to share", key="share_link_out")
    share_link_created(run_id, scopes, ttl)
