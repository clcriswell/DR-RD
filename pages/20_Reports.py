"""Reports and exports page."""

from __future__ import annotations

import io
import json
from zipfile import ZipFile

import streamlit as st

from utils.share_links import viewer_from_query
from utils.redaction import redact_public
from utils.telemetry import log_event, safety_export_blocked

from app.ui import empty_states
from app.ui import safety as ui_safety
from app.ui.a11y import aria_live_region, inject, main_start
from app.ui.command_palette import open_palette
from utils import bundle, report_builder, run_reproduce
from utils import safety as safety_utils
from utils.flags import is_enabled
from utils.i18n import tr as t
from utils.paths import artifact_path, run_root
from utils.query_params import encode_config
from utils.report_html import build_html_report
from utils.runs import last_run_id, load_run_meta
from utils.trace_export import flatten_trace_rows

inject()
main_start()
aria_live_region()

viewer_mode, vinfo = viewer_from_query(dict(st.query_params))
if viewer_mode:
    log_event({"event": "share_link_accessed", "run_id": vinfo.get("rid"), "scopes": vinfo.get("scopes", [])})
    st.info("View only link. Some controls are disabled.")
elif "error" in vinfo:
    if vinfo["error"] == "exp":
        log_event({"event": "share_link_expired"})
    else:
        log_event({"event": "share_link_invalid", "reason": vinfo["error"]})
    st.warning("Invalid or expired share link.")

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
scopes = vinfo.get("scopes", [])
if viewer_mode and "reports" not in scopes:
    st.warning("Reports access not allowed.")
    st.stop()

if not run_id:
    log_event({"event": "nav_page_view", "page": "reports", "run_id": None})
    st.title(t("reports_title"))
    empty_states.reports_empty()
else:
    log_event({"event": "nav_page_view", "page": "reports", "run_id": run_id})
    st.title(t("reports_title"))
    st.caption(t("reports_caption"))

    if not viewer_mode:
        if st.button("Reproduce run", use_container_width=True, help="Prefill inputs from this run"):
            try:
                locked = run_reproduce.load_run_inputs(run_id)
                kwargs = run_reproduce.to_orchestrator_kwargs(locked)
                st.query_params.update(encode_config(kwargs) | {"view": "run", "origin_run_id": run_id})
                st.toast("Prefilled from saved config. Review and start the run.")
                log_event({"event": "reproduce_prep", "run_id": run_id})
            except FileNotFoundError:
                st.toast("Missing run lockfile", icon="⚠️")

    meta = load_run_meta(run_id) or {}
    if meta.get("status") == "resumable" and not viewer_mode:
        st.info("This run can be resumed.")
        if st.button("Resume run", use_container_width=True, help="Continue this run"):
            st.query_params.update({"resume_from": run_id, "view": "run"})
            st.switch_page("app.py")
    trace_path = artifact_path(run_id, "trace", "json")
    trace = json.loads(trace_path.read_text(encoding="utf-8")) if trace_path.exists() else []
    summary_path = artifact_path(run_id, "synth", "md")
    summary_text = summary_path.read_text(encoding="utf-8") if summary_path.exists() else None
    if viewer_mode and summary_text:
        summary_text = redact_public(summary_text)
    totals = {
        "tokens": sum((step.get("tokens") or 0) for step in trace),
        "cost": sum((step.get("cost") or 0.0) for step in trace),
    }
    results = []
    for step in trace:
        if isinstance(step.get("safety"), dict):
            try:
                results.append(safety_utils.SafetyResult(**step["safety"]))
            except Exception:
                pass
    if summary_text:
        results.append(safety_utils.check_text(summary_text))
    agg = (
        safety_utils.merge_results(*results)
        if results
        else safety_utils.SafetyResult([], False, 0.0)
    )
    cfg_s = safety_utils.default_config()
    risky = agg.findings and (
        agg.blocked
        or agg.score >= cfg_s.high_severity_threshold
        or any(f.category in cfg_s.block_categories for f in agg.findings)
    )
    ui_safety.badge(agg, where="export")
    if risky and cfg_s.mode == "block":
        st.info("Export blocked by safety policy")
        safety_export_blocked(run_id, "all", [f.category for f in agg.findings])
        st.stop()
    sanitizer = safety_utils.sanitize_text if agg.findings else None
    md = report_builder.build_markdown_report(
        run_id, meta, trace, summary_text, totals, sanitizer=sanitizer
    )
    if viewer_mode:
        md = redact_public(md)
    rows = flatten_trace_rows(trace)

    with st.expander(t("report_preview_label"), expanded=True):
        st.code(md, language=None)

    def _read_bytes(rid: str, name: str, ext: str) -> bytes:
        if name == "report" and ext == "md":
            data = md
        else:
            path = artifact_path(rid, name, ext)
            if not path.exists():
                raise FileNotFoundError
            data = path.read_text(encoding="utf-8")
        if sanitizer and ext in {"md", "txt", "html", "csv", "json"}:
            data = safety_utils.sanitize_text(data)
            if ext in {"md", "txt"}:
                data += "\n\nSanitized by DR RD."
            elif ext == "html":
                data += "<p>Sanitized by DR RD.</p>"
        return data.encode("utf-8")

    def _list_existing(rid: str):
        root = run_root(rid)
        if not root.exists():
            return []
        return [(p.stem, p.suffix.lstrip(".")) for p in sorted(root.iterdir()) if p.is_file()]

    files = _list_existing(run_id)
    artifacts = [(f"{n}.{e}", f"{n}.{e}") for n, e in files]
    html = build_html_report(run_id, meta, rows, summary_text, totals, artifacts)
    if not files and not summary_text:
        empty_states.reports_empty()
    else:
        bundle_bytes = bundle.build_zip_bundle(
            run_id,
            [],
            read_bytes=_read_bytes,
            list_existing=_list_existing,
            sanitize=lambda n, e, b: b,
        )
        with ZipFile(io.BytesIO(bundle_bytes)) as zf:
            bundle_count = len(zf.namelist())

        if "artifacts" in scopes:
            col_md, col_html, col_zip = st.columns(3)
            if col_md.download_button(
                t("download_report"),
                data=md.encode("utf-8"),
                file_name=f"report_{run_id}.md",
                mime="text/markdown",
                use_container_width=True,
                help=t("report_download_help"),
            ):
                log_event({"event": "export_clicked", "format": "md", "run_id": run_id})
            if col_html.download_button(
                "Download report (.html)",
                data=html.encode("utf-8"),
                file_name=f"report_{run_id}.html",
                mime="text/html",
                use_container_width=True,
                help="Download report as HTML",
            ):
                log_event({"event": "export_clicked", "format": "html", "run_id": run_id})
            if col_zip.download_button(
                t("download_bundle"),
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

            st.caption(
                "Tip: Open the HTML in your browser and use Print \u2192 Save as PDF for a polished PDF."
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
        else:
            st.info("Downloads disabled for this link.")
