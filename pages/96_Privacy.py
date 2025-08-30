"""Privacy & data controls."""

from __future__ import annotations

import streamlit as st

from app.ui.command_palette import open_palette
from utils.telemetry import log_event
from utils import consent as _consent
from utils import retention, prefs, runs


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

if st.query_params.get("view") != "privacy":
    st.query_params["view"] = "privacy"
log_event({"event": "nav_page_view", "page": "privacy"})

st.title("Privacy & Data")

# Section 1: Consent
st.subheader("Consent")
c = _consent.get()
tel = st.checkbox("Allow telemetry", value=bool(c.telemetry) if c else False)
srv = st.checkbox("Allow surveys", value=bool(c.surveys) if c else False)
if st.button("Save consent choices", key="save_consent", type="primary"):
    _consent.set(telemetry=tel, surveys=srv)
    log_event(
        {
            "event": "consent_changed",
            "telemetry": bool(tel),
            "surveys": bool(srv),
        }
    )
    st.success("Saved choices")

# Section 2: Retention
st.subheader("Retention")
pf = prefs.load_prefs()
events_days = st.number_input(
    "Telemetry retention days",
    min_value=7,
    max_value=365,
    value=int(pf["privacy"].get("retention_days_events", 30)),
    key="events_days",
)
runs_days = st.number_input(
    "Run data retention days",
    min_value=7,
    max_value=365,
    value=int(pf["privacy"].get("retention_days_runs", 60)),
    key="runs_days",
)
if st.button("Save retention settings", key="save_retention"):
    pf["privacy"]["retention_days_events"] = int(events_days)
    pf["privacy"]["retention_days_runs"] = int(runs_days)
    prefs.save_prefs(pf)
    st.toast("Retention settings saved")
if st.button("Purge old telemetry", key="purge_events"):
    count = retention.purge_telemetry_older_than(int(events_days))
    log_event(
        {
            "event": "data_purged",
            "scope": "events",
            "days": int(events_days),
            "count": count,
        }
    )
    st.write(f"Removed {count} files")
if st.button("Purge old runs", key="purge_runs"):
    count = retention.purge_runs_older_than(int(runs_days))
    log_event(
        {
            "event": "data_purged",
            "scope": "runs",
            "days": int(runs_days),
            "count": count,
        }
    )
    st.write(f"Removed {count} runs")

# Section 3: Per run deletion
st.subheader("Per run deletion")
run_list = runs.list_runs()
options = [r["run_id"] for r in run_list]
selected = st.selectbox("Run ID", options) if options else None
if selected:
    if st.button("Delete run data", key="del_run_data"):
        existed = retention.delete_run(selected)
        retention.delete_run_events(selected)
        log_event({"event": "run_deleted", "run_id": selected, "scope": "all"})
        st.write("Run deleted" if existed else "Run not found")
    if st.button("Delete run events only", key="del_run_events"):
        count = retention.delete_run_events(selected)
        log_event({"event": "run_deleted", "run_id": selected, "scope": "events"})
        st.write(f"Updated {count} files")

# Section 4: Export
st.subheader("Export")
st.write(
    "Run `python scripts/privacy_export.py --run-id <id> --out <dir>` from the command line to export a run's data."
)

