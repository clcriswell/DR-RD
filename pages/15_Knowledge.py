"""Knowledge Manager page."""

import streamlit as st

from app.ui import knowledge as ui
from app.ui.a11y import aria_live_region, inject, main_start
from app.ui.command_palette import open_palette
from utils import knowledge_store, upload_scan, uploads
from utils import prefs
from utils.embeddings import embed_texts
from utils.rag import index as rag_index, textsplit
from utils.telemetry import index_built, item_reindexed
from utils.i18n import tr as t
from utils.telemetry import (
    knowledge_added,
    knowledge_removed,
    knowledge_tags_updated,
    log_event,
)

inject()
main_start()
aria_live_region()

st.title(t("knowledge_title"))
st.caption("Select sources in Sidebar → Knowledge.")
log_event({"event": "nav_page_view", "page": "knowledge"})

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

knowledge_store.init_store()

st.header("Upload")
files = ui.uploader()
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
removed, tag_updates, reindex_ids = ui.table(items)
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
        chunks = textsplit.split(text, size=prefs_cfg.get("chunk_size", 800), overlap=prefs_cfg.get("chunk_overlap", 120))
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
    chunks = textsplit.split(text, size=prefs_cfg.get("chunk_size", 800), overlap=prefs_cfg.get("chunk_overlap", 120))
    cnt = rag_index.upsert_document(
        item_id,
        {"name": it.get("name"), "tags": it.get("tags", []), "path": it.get("path")},
        chunks,
        embedder=_embedder,
    )
    item_reindexed(item_id, cnt)
    st.toast("Reindexed item")
