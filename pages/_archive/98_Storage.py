import streamlit as st

from utils import prefs, storage

st.title("Storage Settings")

conf = prefs.load_prefs().get("storage", {})
backend = st.selectbox("Backend", ["local", "s3", "gcs"], index=["local", "s3", "gcs"].index(conf.get("backend", "gcs")))
bucket = st.text_input("Bucket", conf.get("bucket", ""))
prefix = st.text_input("Prefix", conf.get("prefix", "dr_rd"))
ttl = st.number_input("Signed URL TTL", value=int(conf.get("signed_url_ttl_sec", 600)))

if st.button("Save"):
    p = prefs.load_prefs()
    p["storage"] = {
        "backend": backend,
        "bucket": bucket,
        "prefix": prefix,
        "signed_url_ttl_sec": int(ttl),
    }
    prefs.save_prefs(p)
    st.success("Saved")

st.write("Current backend:", storage.get_storage().backend)
