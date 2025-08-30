from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from utils import runs_index, run_notes
from utils.telemetry import (
    log_event,
    history_filter_changed,
    history_export_clicked,
    run_annotated,
    run_favorited,
)
from app.ui.command_palette import open_palette

# quick open via button
if st.button(
    "⌘K Command palette",
    key="cmd_btn",
    use_container_width=False,
    help="Open global search",
):
    log_event({"event": "palette_opened"})
    open_palette()

# auto open via query param
if st.query_params.get("cmd") == "1":
    log_event({"event": "palette_opened", "source": "qp"})
    open_palette()
    st.query_params.pop("cmd", None)

act = st.session_state.pop("_cmd_action", None)
if act:
    if act["action"] == "switch_page":
        st.switch_page(act["params"]["page"])
    elif act["action"] == "set_params":
        st.query_params.update(act["params"])
        st.rerun()
    elif act["action"] == "copy":
        st.code(act["params"]["text"], language=None)
        st.toast("Copied link")
    elif act["action"] == "start_demo":
        st.query_params.update({"mode": "demo", "view": "run"})
        st.toast("Demo mode selected. Review and start.")
    log_event(
        {
            "event": "palette_executed",
            "kind": act.get("kind"),
            "action": act["action"],
        }
    )

params = dict(st.query_params)

st.title("Run History")
log_event({"event": "nav_page_view", "page": "history"})

notes_lookup = run_notes.all_notes()
index = runs_index.load_index()

status_options = sorted({r["status"] for r in index if r.get("status")})
mode_options = sorted({r["mode"] for r in index if r.get("mode")})
all_tags = sorted({t for n in notes_lookup.values() for t in n.get("tags", [])})

q_default = params.get("q", "")
status_default = params.get("status", "")
fav_default = params.get("fav", "0") == "1"

status_default_list = [s for s in status_default.split(",") if s]

q_val = st.text_input("Search", q_default)
status_val = st.multiselect("Status", status_options, default=status_default_list)
mode_val = st.multiselect("Mode", mode_options)
dates = st.date_input("Date range", value=(None, None))
tags_val = st.multiselect("Tags", all_tags)
fav_val = st.checkbox("Favorites only", value=fav_default)

qp_changed = (
    q_val != q_default
    or set(status_val) != set(status_default_list)
    or fav_val != fav_default
)
if qp_changed:
    st.query_params["q"] = q_val
    st.query_params["status"] = ",".join(status_val)
    st.query_params["fav"] = "1" if fav_val else "0"
    history_filter_changed(len(q_val), len(status_val), len(mode_val), fav_val)
    st.rerun()

date_from = None
date_to = None
if isinstance(dates, tuple):
    if dates[0]:
        date_from = datetime.combine(dates[0], datetime.min.time()).timestamp()
    if dates[1]:
        date_to = datetime.combine(dates[1], datetime.max.time()).timestamp()

rows = runs_index.search(
    index,
    q=q_val,
    status=status_val,
    mode=mode_val,
    date_from=date_from,
    date_to=date_to,
    favorites_only=fav_val,
    tags=tags_val,
    notes_lookup=notes_lookup,
)

if rows:
    df = pd.DataFrame(
        [
            {
                "⭐": "★" if notes_lookup.get(r["run_id"], {}).get("favorite") else "",
                "run_id": r["run_id"],
                "started_at": datetime.fromtimestamp(r["started_at"]).isoformat()
                if r.get("started_at")
                else "",
                "duration": (r.get("completed_at", 0) - r.get("started_at", 0))
                if r.get("completed_at") and r.get("started_at")
                else None,
                "status": r.get("status"),
                "mode": r.get("mode"),
                "idea_preview": r.get("idea_preview", "")[:40],
                "tokens": r.get("tokens"),
                "cost": r.get("cost_usd"),
                "Trace": f"./?view=trace&run_id={r['run_id']}",
                "Reports": f"./?view=reports&run_id={r['run_id']}",
                "Reproduce": f"./?view=run&origin_run_id={r['run_id']}",
                "Resume": f"./?view=run&resume_from={r['run_id']}"
                if r.get("status") == "resumable"
                else "",
            }
            for r in rows
        ]
    )
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Trace": st.column_config.LinkColumn("Trace"),
            "Reports": st.column_config.LinkColumn("Reports"),
            "Reproduce": st.column_config.LinkColumn("Reproduce"),
            "Resume": st.column_config.LinkColumn("Resume"),
        },
    )
else:
    st.info("No runs match.")

if rows and st.button("Export CSV"):
    csv_bytes = runs_index.to_csv(rows)
    history_export_clicked(len(rows))
    st.download_button(
        "runs.csv",
        data=csv_bytes,
        file_name="runs.csv",
        mime="text/csv",
    )

if rows:
    sel_run = st.sidebar.selectbox("Annotate run", [r["run_id"] for r in rows])
    note = run_notes.load(sel_run)
    title = st.sidebar.text_input("Title", value=note.get("title", ""))
    tags = st.sidebar.text_input("Tags", value=",".join(note.get("tags", [])))
    favorite = st.sidebar.checkbox("Favorite", value=note.get("favorite", False))
    body = st.sidebar.text_area("Note", value=note.get("note", ""))
    if st.sidebar.button("Save"):
        saved = run_notes.save(
            sel_run,
            title=title,
            note=body,
            tags=[t.strip() for t in tags.split(",") if t.strip()],
            favorite=favorite,
        )
        run_annotated(
            sel_run,
            len(saved.get("title", "")),
            len(saved.get("tags", [])),
            len(saved.get("note", "")),
            saved.get("favorite", False),
        )
        st.sidebar.success("Saved")
        notes_lookup[sel_run] = saved
        st.rerun()
    if st.sidebar.button("Toggle Favorite"):
        toggled = run_notes.toggle_favorite(sel_run)
        run_favorited(sel_run, toggled.get("favorite", False))
        st.sidebar.success("Updated")
        st.rerun()
