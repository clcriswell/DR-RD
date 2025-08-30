import json
from contextlib import contextmanager

import streamlit as st

from app.ui.a11y import aria_live_region
from utils.errors import SafeError, as_json


class _StatusBox:
    def __init__(self, status_obj):
        self._status = status_obj

    def update(self, label: str | None = None, state: str | None = None) -> None:
        kwargs = {}
        if label is not None:
            kwargs["label"] = label
        if state is not None:
            kwargs["state"] = state
        if kwargs:
            self._status.update(**kwargs)


@contextmanager
def stage_status(label: str, expanded: bool = False):
    status = st.status(label, expanded=expanded)
    box = _StatusBox(status)
    try:
        yield box
    finally:
        pass


def step_progress(total_steps: int):
    bar = st.progress(0, text="Run progress")
    region_id = aria_live_region("progress")

    def update(i: int, text: str):
        pct = int(i * 100 / total_steps)
        bar.progress(pct, text=text)
        st.markdown(
            f"<script>document.getElementById('{region_id}').innerText = {json.dumps(text)};</script>",
            unsafe_allow_html=True,
        )

    return update


def help_once(key: str, text: str) -> None:
    flag = f"_help_{key}"
    if not st.session_state.get(flag):
        st.caption(text)
        st.session_state[flag] = True


def error_banner(err: SafeError):
    st.error(f"{err.user_message}  \nSupport ID: `{err.support_id}`")
    with st.expander("Show technical details"):
        st.code(err.tech_message or "", language=None)
        if err.traceback:
            st.code(err.traceback, language=None)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.download_button(
            "Download error report (.json)",
            data=as_json(err),
            file_name=f"error_{err.support_id}.json",
            mime="application/json",
            use_container_width=True,
        )
    return True
