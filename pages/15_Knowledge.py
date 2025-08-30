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

st.title("Knowledge Manager")
st.caption("Select sources in Sidebar → Knowledge.")
log_event({"event": "nav_page_view", "page": "knowledge"})
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
