from pathlib import Path
import subprocess

import yaml
import streamlit as st
from utils.telemetry import (
    log_event,
    prompt_preview,
    prompt_bump,
    prompt_saved,
    prompt_edited,
)
from utils.prompts import loader, runtime, versioning

log_event({"event": "nav_page_view", "page": "prompts"})

st.title("Prompts")

prompts = loader.load_all()
rows = [
    {
        "id": p["id"],
        "version": p["version"],
        "title": p.get("title", ""),
        "last_change": (p.get("changelog") or ["?"])[-1],
    }
    for p in prompts.values()
]
st.dataframe(rows)

ids = list(prompts.keys())
sel = st.selectbox("Select prompt", [""] + ids)
if sel:
    prompt_preview(sel)
    obj = prompts[sel]
    tabs = st.tabs(["Preview", "History & Diff"])
    with tabs[0]:
        vals = {}
        for var in obj.get("vars", []):
            name = var.get("name")
            default = var.get("default", "")
            vals[name] = st.text_input(name, default)
        text, _ = runtime.render(sel, vals)
        st.text_area("Rendered", text, height=200)
        st.button("Copy", on_click=lambda: st.session_state.update({"_": text}))
    with tabs[1]:
        st.markdown("### Current template")
        st.code(obj.get("template", ""))
        try:
            old = subprocess.check_output(
                ["git", "show", f"HEAD:prompts/{sel}.yaml"], text=True
            )
        except Exception:
            old = ""
        diff = versioning.unified_diff(old, Path(f"prompts/{sel}.yaml").read_text())
        st.markdown("### Diff vs HEAD")
        st.code(diff or "(no diff)")
        part = st.selectbox("Bump", ["patch", "minor", "major"], key="bump")
        new_template = st.text_area("Template", obj.get("template", ""))
        if st.button("Save"):
            old_version = obj["version"]
            new_version = versioning.next_version(old_version, part)
            obj["version"] = new_version
            obj["template"] = new_template
            obj.setdefault("changelog", []).append(f"{new_version}: edited")
            Path(f"prompts/{sel}.yaml").write_text(
                yaml.safe_dump(obj, sort_keys=False)
            )
            prompt_bump(sel, old_version, new_version)
            prompt_saved(sel, new_version)
            prompt_edited(sel, new_version)
            st.success("Saved")
            st.experimental_rerun()
