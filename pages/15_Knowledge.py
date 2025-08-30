"""Knowledge Manager page."""

import streamlit as st

from app.ui import knowledge as ui
from utils import knowledge_store, uploads
from utils.telemetry import (
    knowledge_added,
    knowledge_removed,
    knowledge_tags_updated,
    log_event,
)
from utils.i18n import tr as t
from app.ui.command_palette import open_palette

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
        item = knowledge_store.add_item(f.name, dest, tags=tag_list, kind="upload")
        knowledge_added(item["id"], item["name"], item["type"], item["size"])
        st.toast(f"Uploaded {f.name}")

st.header("Your sources")
items = knowledge_store.list_items()
removed, tag_updates = ui.table(items)
for item_id in removed:
    if knowledge_store.remove_item(item_id):
        knowledge_removed(item_id)
        st.toast("Removed item")
for item_id, tags in tag_updates.items():
    knowledge_store.set_tags(item_id, tags)
    knowledge_tags_updated(item_id, len(tags))
    st.toast("Tags updated")
