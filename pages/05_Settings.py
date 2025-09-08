"""Unified settings page with multiple sections."""

from __future__ import annotations

import copy
import json
import os
from datetime import datetime

import streamlit as st

from app.ui import knowledge as knowledge_ui
from app.ui.a11y import aria_live_region, inject, main_start
from app.ui.command_palette import open_palette
from utils import knowledge_store, prefs, upload_scan, uploads, providers, consent as _consent, retention, runs, storage, health_check
from utils.embeddings import embed_texts
from utils.i18n import get_locale, set_locale
from utils.i18n import tr as t
from utils.lazy_import import local_import
from utils.prefs import DEFAULT_PREFS, load_prefs, save_prefs
from utils.rag import index as rag_index
from utils.rag import textsplit
from utils.telemetry import (
    index_built,
    item_reindexed,
    knowledge_added,
    knowledge_removed,
    knowledge_tags_updated,
    log_event,
)
from utils.validate_providers import quick_probe
from dr_rd.config.env import get_env

st.set_page_config(page_title="Settings")
inject()
main_start()
aria_live_region()

# Command palette controls (shared across sections)
if st.button(
    "⌘K Command palette",
    key="cmd_btn",
    width="content",
    help="Open global search",
):
    log_event({"event": "palette_opened"})
    open_palette()

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
        {"event": "palette_executed", "kind": act.get("kind"), "action": act["action"]}
    )

st.title("Settings")


def render_general_settings() -> None:
    if st.query_params.get("view") != "settings":
        st.query_params["view"] = "settings"
    log_event({"event": "nav_page_view", "page": "settings"})

    prefs_data = load_prefs()
    lang = st.selectbox(
        "Language",
        ["en", "es"],
        index=["en", "es"].index(get_locale()),
        help="UI language",
    )
    if st.button("Apply language", help="Apply selected language"):
        set_locale(lang)
        prefs_data["ui"]["language"] = lang
        save_prefs(prefs_data)
        log_event({"event": "locale_changed", "lang": lang})
        st.rerun()

    st.subheader("Defaults for new runs")
    mode = "standard"
    max_tokens = st.number_input(
        t("max_tokens_label"),
        min_value=0,
        step=100,
        value=prefs_data["defaults"].get("max_tokens") or 0,
        help=t("max_tokens_help"),
    )
    budget_limit = st.number_input(
        t("budget_limit_label"),
        min_value=0.0,
        step=0.5,
        value=prefs_data["defaults"].get("budget_limit_usd") or 0.0,
        help=t("budget_limit_help"),
    )
    ks_defaults = set(prefs_data["defaults"].get("knowledge_sources", []))
    ks_samples = st.checkbox(
        "Samples",
        value="samples" in ks_defaults,
        key="pref_samples",
    )
    connectors_enabled = bool(os.getenv("CONNECTORS_CONFIGURED"))
    ks_connectors = st.checkbox(
        "Connectors",
        value="connectors" in ks_defaults and connectors_enabled,
        disabled=not connectors_enabled,
        key="pref_connectors",
        help="Configure connectors in Settings → Providers",
    )
    ks_uploads = st.checkbox(
        "Uploads",
        value="uploads" in ks_defaults,
        key="pref_uploads",
    )
    knowledge_sources = []
    if ks_samples:
        knowledge_sources.append("samples")
    if ks_connectors:
        knowledge_sources.append("connectors")
    if ks_uploads:
        knowledge_sources.append("uploads")

    st.subheader("UI behavior")
    show_trace = st.checkbox(
        t("show_trace_label"),
        value=prefs_data["ui"].get("show_trace_by_default", True),
        help=t("show_trace_help"),
    )
    auto_export = st.checkbox(
        t("auto_export_label"),
        value=prefs_data["ui"].get("auto_export_on_completion", False),
        help=t("auto_export_help"),
    )
    trace_page_size = st.number_input(
        t("trace_page_size_label"),
        min_value=10,
        max_value=200,
        value=prefs_data["ui"].get("trace_page_size", 50),
        help=t("trace_page_size_help"),
    )

    st.subheader("Privacy")
    telemetry = st.checkbox(
        t("telemetry_label"),
        value=prefs_data["privacy"].get("telemetry_enabled", True),
        help=t("telemetry_help"),
    )
    share_adv = st.checkbox(
        t("share_adv_label"),
        value=prefs_data["privacy"].get("include_advanced_in_share_links", False),
        help=t("share_adv_help"),
    )

    updated = {
        "version": DEFAULT_PREFS["version"],
        "defaults": {
            "mode": mode,
            "max_tokens": int(max_tokens) if max_tokens is not None else None,
            "budget_limit_usd": float(budget_limit) if budget_limit else None,
            "knowledge_sources": knowledge_sources,
        },
        "ui": {
            "show_trace_by_default": bool(show_trace),
            "auto_export_on_completion": bool(auto_export),
            "trace_page_size": int(trace_page_size),
            "language": prefs_data["ui"].get("language", "en"),
        },
        "privacy": {
            "telemetry_enabled": bool(telemetry),
            "include_advanced_in_share_links": bool(share_adv),
        },
    }

    if st.button(t("save_prefs_label"), type="primary", help=t("save_prefs_help")):
        save_prefs(updated)
        log_event({"event": "settings_changed"})
        st.success(t("prefs_saved_msg"))

    if st.button(t("restore_defaults_label"), help=t("restore_defaults_help")):
        save_prefs(DEFAULT_PREFS)
        log_event({"event": "settings_changed", "scope": "restore"})
        st.success(t("prefs_restored_msg"))

    uploaded = st.file_uploader(t("import_prefs_label"), type="json", help=t("import_prefs_help"))
    if uploaded is not None:
        try:
            data = json.load(uploaded)
            save_prefs(data)
            log_event({"event": "settings_imported", "version": data.get("version")})
            st.success(t("prefs_imported_msg"))
        except Exception:
            st.error(t("prefs_invalid_msg"))

    if st.download_button(
        t("export_prefs_label"),
        data=json.dumps(prefs_data).encode("utf-8"),
        file_name="config.json",
        help=t("export_prefs_help"),
    ):
        log_event({"event": "settings_exported", "version": prefs_data.get("version")})


def render_knowledge() -> None:
    knowledge_store.init_store()
    st.caption("Select sources in Sidebar → Knowledge.")
    log_event({"event": "nav_page_view", "page": "knowledge"})

    st.header("Upload")
    files = knowledge_ui.uploader()
    tags_text = st.text_input("Tags", key="upload_tags", help="Comma-separated tags")
    if st.button("Add files"):
        tag_list = [t.strip() for t in tags_text.split(",") if t.strip()]
        for f in files or []:
            if not uploads.allowed_ext(f.name):
                st.warning(f"Unsupported file type: {f.name}")
                continue
            dest = uploads.unique_upload_path(f.name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("wb") as out:
                out.write(f.getbuffer())
            if not upload_scan.allowed(dest):
                st.warning(f"Unsupported file type or size: {f.name}")
                dest.unlink(missing_ok=True)
                continue
            pii_flag = False
            typ = upload_scan.sniff_type(dest)
            if typ in {"text/plain", "text/markdown", "application/json", "text/csv"}:
                try:
                    with dest.open("r", encoding="utf-8", errors="ignore") as fh:
                        head = fh.read(200_000)
                    pii_flag = upload_scan.detect_pii(head)
                except Exception:
                    pii_flag = False
            item = knowledge_store.add_item(
                f.name, dest, tags=tag_list, kind="upload", pii_flag=pii_flag
            )
            knowledge_added(item["id"], item["name"], item["type"], item["size"])
            st.toast(f"Uploaded {f.name}")

    st.header("Your sources")
    items = knowledge_store.list_items()
    removed, tag_updates, reindex_ids = knowledge_ui.table(items)
    for item_id in removed:
        if knowledge_store.remove_item(item_id):
            knowledge_removed(item_id)
            st.toast("Removed item")
    for item_id, tags in tag_updates.items():
        knowledge_store.set_tags(item_id, tags)
        knowledge_tags_updated(item_id, len(tags))
        st.toast("Tags updated")

    prefs_cfg = prefs.load_prefs().get("retrieval", {})
    rag_index.init()
    with rag_index._conn() as c:
        doc_count = c.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunk_count = c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    st.caption(f"Index: {doc_count} docs, {chunk_count} chunks")

    def _embedder(chunks: list[str]):
        if not prefs_cfg.get("use_embeddings"):
            return None
        return embed_texts(
            chunks,
            provider=prefs_cfg.get("embedding_provider", "openai"),
            model=prefs_cfg.get("embedding_model", "text-embedding-3-small"),
        )

    if st.button("Build/Refresh index"):
        total_chunks = 0
        for it in items:
            text = knowledge_store.load_text(it["id"], max_chars=prefs_cfg.get("max_chars_per_doc"))
            if not text:
                continue
            chunks = textsplit.split(
                text, size=prefs_cfg.get("chunk_size", 800), overlap=prefs_cfg.get("chunk_overlap", 120)
            )
            cnt = rag_index.upsert_document(
                it["id"],
                {"name": it.get("name"), "tags": it.get("tags", []), "path": it.get("path")},
                chunks,
                embedder=_embedder,
            )
            total_chunks += cnt
        index_built(len(items), total_chunks)
        st.toast(f"Indexed {len(items)} items ({total_chunks} chunks)")

    for item_id in reindex_ids:
        text = knowledge_store.load_text(item_id, max_chars=prefs_cfg.get("max_chars_per_doc"))
        if not text:
            continue
        it = knowledge_store.get_item(item_id) or {}
        chunks = textsplit.split(
            text, size=prefs_cfg.get("chunk_size", 800), overlap=prefs_cfg.get("chunk_overlap", 120)
        )
        cnt = rag_index.upsert_document(
            item_id,
            {"name": it.get("name"), "tags": it.get("tags", []), "path": it.get("path")},
            chunks,
            embedder=_embedder,
        )
        item_reindexed(item_id, cnt)
        st.toast("Reindexed item")


def render_providers() -> None:
    rows = []
    for prov, info in providers.available_providers().items():
        secret = "✅" if providers.has_secrets(prov) else "⚠️"
        for model in info.get("models", {}):
            price = providers.model_price(prov, model)
            rows.append(
                {
                    "Provider": prov,
                    "Secret": secret,
                    "Model": model,
                    "In $/1k": price.get("input_per_1k", 0.0),
                    "Out $/1k": price.get("output_per_1k", 0.0),
                }
            )
    st.dataframe(rows, hide_index=True)

    prefs_data = prefs.load_prefs()
    sel = providers.from_prefs_snapshot(
        prefs_data.get("defaults", {}).get("provider_model", {})
    ) or providers.default_model_for_mode("standard")
    cur_provider, cur_model = sel

    prov = st.selectbox(
        "Provider",
        list(providers.available_providers().keys()),
        index=list(providers.available_providers().keys()).index(cur_provider),
    )
    models = list(providers.list_models(prov).keys())
    model_idx = models.index(cur_model) if cur_model in models else 0
    mdl = st.selectbox("Model", models, index=model_idx)

    status = st.empty()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Validate"):
            result = quick_probe(prov, mdl)
            log_event(
                {
                    "event": "provider_validated",
                    "provider": prov,
                    "model": mdl,
                    "status": result.get("status"),
                }
            )
            status.write(result.get("status"))
    with col2:
        if st.button("Save as default"):
            snap = providers.to_prefs_snapshot(prov, mdl)
            prefs_data["defaults"]["provider_model"] = snap
            prefs.save_prefs(prefs_data)
            log_event({"event": "provider_default_changed", "provider": prov, "model": mdl})
            status.success("Saved")

    st.caption(
        "Orchestrators read this selection by default; runs may override via mode or advanced settings."
    )


def render_privacy() -> None:
    st.subheader("Consent")
    c = _consent.get()
    tel = st.checkbox("Allow telemetry", value=bool(c.telemetry) if c else False)
    srv = st.checkbox("Allow surveys", value=bool(c.surveys) if c else False)
    if st.button("Save consent choices", key="save_consent", type="primary"):
        _consent.set(telemetry=tel, surveys=srv)
        log_event({"event": "consent_changed", "telemetry": bool(tel), "surveys": bool(srv)})
        st.success("Saved choices")

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

    st.subheader("Export")
    st.write(
        "Run `python scripts/privacy_export.py --run-id <id> --out <dir>` from the command line to export a run's data."
    )


def render_storage() -> None:
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


def render_health() -> None:
    st.title(t("health_title"))
    if st.button("Run diagnostics", help="Run system diagnostics"):
        report = health_check.run_all()
        cols = st.columns(3)
        cols[0].metric("pass", report.summary.get("pass", 0))
        cols[1].metric("warn", report.summary.get("warn", 0))
        cols[2].metric("fail", report.summary.get("fail", 0))
        pd = local_import("pandas")
        df = pd.DataFrame(
            [{"id": c.id, "name": c.name, "status": c.status} for c in report.checks]
        )
        st.dataframe(df, width="stretch")
        for c in report.checks:
            with st.expander(c.name):
                st.write(c.details)
                if c.remedy:
                    st.caption(c.remedy)
        st.download_button(
            "health_report.json",
            data=health_check.to_json(report),
            file_name="health_report.json",
            mime="application/json",
        )
        st.download_button(
            "health_report.md",
            data=health_check.to_markdown(report),
            file_name="health_report.md",
            mime="text/markdown",
        )
        log_event({"event": "health_check_run", "summary": report.summary})
        if get_env("NO_NET") == "1":
            st.caption("Network tests skipped")
    else:
        st.write("Click to run diagnostics")


# Render sections via tabs
sections = st.tabs(["Settings", "Knowledge", "Providers", "Privacy", "Storage", "Health"])
with sections[0]:
    render_general_settings()
with sections[1]:
    render_knowledge()
with sections[2]:
    render_providers()
with sections[3]:
    render_privacy()
with sections[4]:
    render_storage()
with sections[5]:
    render_health()
