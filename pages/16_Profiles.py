import json
import time

import streamlit as st

from utils import prefs, profiles
from utils.telemetry import (
    log_event,
    profile_applied,
    profile_deleted,
    profile_saved,
    profile_set_default,
)

log_event({"event": "nav_page_view", "page": "profiles"})

st.title("Profiles")

profs = profiles.list_profiles()
for pr in profs:
    defaults = pr.data.get("defaults", {})
    pm = defaults.get("provider_model", {})
    summary = {
        "mode": defaults.get("mode"),
        "provider": pm.get("provider"),
        "model": pm.get("model"),
        "budget": defaults.get("budget_limit_usd"),
    }
    with st.expander(pr.name, expanded=False):
        st.write(pr.data.get("description", ""))
        st.write(time.strftime("%Y-%m-%d %H:%M", time.gmtime(pr.data.get("updated_at", 0))))
        st.json(summary)
        c1, c2, c3, c4, c5 = st.columns(5)
        if c1.button("Apply", key=f"ap_{pr.name}"):
            st.query_params["profile"] = pr.name
            profile_applied(pr.name)
            st.switch_page("app.py")
        new_nm = c2.text_input("Rename", pr.name, key=f"rn_{pr.name}")
        if c2.button("Save", key=f"rn_btn_{pr.name}") and new_nm and new_nm != pr.name:
            profiles.save(new_nm, defaults, pr.data.get("description", ""))
            profiles.delete(pr.name)
            profile_saved(new_nm)
            profile_deleted(pr.name)
            st.rerun()
        raw = c3.text_area("Edit JSON", json.dumps(pr.data, indent=2), key=f"ed_{pr.name}")
        if c3.button("Update", key=f"ed_btn_{pr.name}"):
            try:
                obj = json.loads(raw)
                profiles.save(pr.name, obj.get("defaults", {}), obj.get("description", ""))
                profile_saved(pr.name)
                st.rerun()
            except Exception:
                c3.error("Invalid JSON")
        if st.session_state.get(f"del_{pr.name}"):
            if c4.button("Confirm delete", key=f"del_c_{pr.name}"):
                profiles.delete(pr.name)
                profile_deleted(pr.name)
                st.session_state.pop(f"del_{pr.name}")
                st.rerun()
        elif c4.button("Delete", key=f"del_{pr.name}"):
            st.session_state[f"del_{pr.name}"] = True
        if c5.button("Set as default", key=f"def_{pr.name}"):
            pf = prefs.load_prefs()
            pf.setdefault("defaults", {})["profile"] = pr.name
            prefs.save_prefs(pf)
            profile_set_default(pr.name)
            st.success("Default updated")
