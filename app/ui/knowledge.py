import streamlit as st
from datetime import datetime
from utils import uploads


def _fmt_size(size: int) -> str:
    return f"{int(size / 1024)} KB"


def table(items: list[dict]):
    removed: list[str] = []
    tag_updates: dict[str, list[str]] = {}
    for it in items:
        cols = st.columns([3, 1, 1, 2, 2, 1, 1])
        cols[0].write(it["name"])
        cols[1].write(it["type"])
        cols[2].write(_fmt_size(it["size"]))
        new_tags = tag_editor(it["id"], it.get("tags", []), key=f"tags_{it['id']}")
        if new_tags != it.get("tags", []):
            tag_updates[it["id"]] = new_tags
        cols[4].write(datetime.fromtimestamp(it["created_at"]).strftime("%Y-%m-%d %H:%M"))
        if cols[5].button("Remove", key=f"rm_{it['id']}"):
            removed.append(it["id"])
        with open(it["path"], "rb") as fh:
            cols[6].download_button(
                "Download", fh, file_name=it["name"], key=f"dl_{it['id']}"
            )
    return removed, tag_updates


def uploader():
    return st.file_uploader(
        "Upload files", accept_multiple_files=True, type=[e.lstrip(".") for e in uploads.SAFE_EXTS]
    )


def tag_editor(item_id: str, tags: list[str], *, key: str | None = None) -> list[str]:
    text = st.text_input(
        "Tags",
        value=", ".join(tags),
        key=key or f"tags_{item_id}",
        label_visibility="collapsed",
    )
    return [t.strip() for t in text.split(",") if t.strip()]
