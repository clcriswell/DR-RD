import streamlit as st

from utils.global_search import search, resolve_action
from utils.telemetry import log_event
from utils.session_store import SessionStore


def open_palette():
    view_store = SessionStore(
        "view",
        defaults={"trace_view": "summary", "trace_query": "", "palette_open": False},
        persist_keys={"trace_view", "trace_query"},
    )
    view_store.set("palette_open", True)

    @st.dialog("Command palette")
    def _dlg():
        q = st.text_input("Type a command, page, run, or source", key="cmd_q")
        log_event({"event": "palette_query", "q_len": len(q or "")})
        results = search(q) if q else search("")[:10]
        for i, r in enumerate(results):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{r['label']}**  \n{r.get('hint','')}")
            with col2:
                if st.button("Select", key=f"sel_{i}", use_container_width=True):
                    act = resolve_action(r)
                    st.session_state["_cmd_action"] = act
                    st.rerun()
    _dlg()
    view_store.set("palette_open", False)
