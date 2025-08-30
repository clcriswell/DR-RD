"""Reports and exports page."""

from __future__ import annotations

import io
import json
from zipfile import ZipFile

import streamlit as st

from app.ui import empty_states
from app.ui.copy import t
from utils import bundle, report_builder, run_reproduce
from utils.paths import artifact_path, run_root
from utils.query_params import encode_config
from utils.runs import last_run_id, load_run_meta
from utils.telemetry import log_event
from utils.flags import is_enabled
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
if not is_enabled("reports_page", params=params):
    st.warning("Reports page disabled")
    st.stop()

run_id = params.get("run_id") or last_run_id()

if not run_id:
    log_event({"event": "nav_page_view", "page": "reports", "run_id": None})
    st.title(t("reports_title"))
    empty_states.reports_empty()
else:
    log_event({"event": "nav_page_view", "page": "reports", "run_id": run_id})
    st.title(t("reports_title"))
    st.caption(t("reports_caption"))

    if st.button("Reproduce run", use_container_width=True):
        try:
            locked = run_reproduce.load_run_inputs(run_id)
            kwargs = run_reproduce.to_orchestrator_kwargs(locked)
            st.query_params.update(encode_config(kwargs) | {"view": "run", "origin_run_id": run_id})
            st.toast("Prefilled from saved config. Review and start the run.")
            log_event({"event": "reproduce_prep", "run_id": run_id})
        except FileNotFoundError:
            st.toast("Missing run lockfile", icon="⚠️")

    meta = load_run_meta(run_id) or {}
    if meta.get("status") == "resumable":
        st.info("This run can be resumed.")
        if st.button("Resume run", use_container_width=True):
            st.query_params.update({"resume_from": run_id, "view": "run"})
            st.switch_page("app.py")
    trace_path = artifact_path(run_id, "trace", "json")
    trace = json.loads(trace_path.read_text(encoding="utf-8")) if trace_path.exists() else []
    summary_path = artifact_path(run_id, "synth", "md")
    summary_text = summary_path.read_text(encoding="utf-8") if summary_path.exists() else None
    totals = {
        "tokens": sum((step.get("tokens") or 0) for step in trace),
        "cost": sum((step.get("cost") or 0.0) for step in trace),
    }
    md = report_builder.build_markdown_report(run_id, meta, trace, summary_text, totals)

    with st.expander(t("report_preview_label"), expanded=True):
        st.code(md, language=None)

    def _read_bytes(rid: str, name: str, ext: str) -> bytes:
        if name == "report" and ext == "md":
            return md.encode("utf-8")
        path = artifact_path(rid, name, ext)
        if not path.exists():
            raise FileNotFoundError
        return path.read_bytes()

    def _list_existing(rid: str):
        root = run_root(rid)
        if not root.exists():
            return []
        return [(p.stem, p.suffix.lstrip(".")) for p in sorted(root.iterdir()) if p.is_file()]

    files = _list_existing(run_id)
    if not files and not summary_text:
        empty_states.reports_empty()
    else:
        bundle_bytes = bundle.build_zip_bundle(
            run_id, [], read_bytes=_read_bytes, list_existing=_list_existing
        )
        with ZipFile(io.BytesIO(bundle_bytes)) as zf:
            bundle_count = len(zf.namelist())

        col_md, col_zip = st.columns(2)
        if col_md.download_button(
            t("download_report_label"),
            data=md.encode("utf-8"),
            file_name=f"report_{run_id}.md",
            mime="text/markdown",
            use_container_width=True,
            help=t("report_download_help"),
        ):
            log_event({"event": "export_clicked", "format": "md", "run_id": run_id})
        if col_zip.download_button(
            t("download_bundle_label"),
            data=bundle_bytes,
            file_name=f"artifacts_{run_id}.zip",
            mime="application/zip",
            use_container_width=True,
            help=t("bundle_download_help"),
        ):
            log_event(
                {
                    "event": "export_clicked",
                    "format": "zip",
                    "run_id": run_id,
                    "count": bundle_count,
                }
            )

        if files:
            st.subheader(t("artifacts_subheader"))
            for name, ext in files:
                path = artifact_path(run_id, name, ext)
                st.download_button(
                    f"{name}.{ext}",
                    data=path.read_bytes(),
                    file_name=path.name,
                    use_container_width=True,
                    key=path.name,
                    help=t("bundle_download_help"),
                )
