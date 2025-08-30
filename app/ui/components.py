import streamlit as st
from contextlib import contextmanager


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

    def update(i: int, text: str):
        pct = int(i * 100 / total_steps)
        bar.progress(pct, text=text)

    return update


def help_once(key: str, text: str) -> None:
    flag = f"_help_{key}"
    if not st.session_state.get(flag):
        st.caption(text)
        st.session_state[flag] = True
