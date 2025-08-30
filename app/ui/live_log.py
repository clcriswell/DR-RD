import streamlit as st
from utils.stream_events import Event, is_terminal


def render(events_iter):
    """
    Render streaming output. Prefer st.write_stream if available, else manual updates.
    Do not contain business logic.
    """
    out = st.empty()
    buf = ""

    def _write(piece: str):
        nonlocal buf
        buf += piece
        out.markdown(buf)

    if hasattr(st, "write_stream"):
        def gen():
            for e in events_iter:
                if e.kind == "token":
                    yield e.text or ""
                elif e.kind == "message":
                    yield (e.text or "") + "\n"
                if is_terminal(e):
                    break
        st.write_stream(gen())
    else:
        for e in events_iter:
            if e.kind == "token":
                _write(e.text or "")
            elif e.kind == "message":
                _write((e.text or "") + "\n")
            if is_terminal(e):
                break


__all__ = ["render"]
