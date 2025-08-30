from __future__ import annotations

import uuid
from pathlib import Path

import streamlit as st

USER_ID_PATH = Path('.dr_rd/user_id.txt')


def get_user_id() -> str:
    uid = st.session_state.get('user_id')
    if uid:
        return uid
    if USER_ID_PATH.exists():
        uid = USER_ID_PATH.read_text(encoding='utf-8').strip()
    else:
        USER_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
        uid = uuid.uuid4().hex
        USER_ID_PATH.write_text(uid, encoding='utf-8')
    st.session_state['user_id'] = uid
    return uid
