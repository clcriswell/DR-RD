import json
import time

import streamlit as st

from utils import session_store


def test_snapshot_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store, "SESS_DIR", tmp_path / "sess")
    session_store.SESS_DIR.mkdir(parents=True, exist_ok=True)
    st.session_state.clear()
    store = session_store.SessionStore("run", defaults={"foo": 0}, persist_keys={"foo"})
    store.set("foo", 1)
    snap = session_store.SESS_DIR / f"{store.sid}_run.json"
    assert snap.exists()
    sid = store.sid
    st.session_state.clear()
    st.session_state["session_id"] = sid
    store2 = session_store.SessionStore("run", defaults={"foo": 0}, persist_keys={"foo"})
    assert store2.get("foo") == 1


def test_seed_missing_only(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store, "SESS_DIR", tmp_path / "sess2")
    session_store.SESS_DIR.mkdir(parents=True, exist_ok=True)
    st.session_state.clear()
    store = session_store.SessionStore("run", defaults={"a": None, "b": 0})
    store.seed({"a": 1, "b": 2})
    assert store.get("a") == 1
    assert store.get("b") == 0


def test_ttl_logic(tmp_path, monkeypatch):
    monkeypatch.setattr(session_store, "SESS_DIR", tmp_path / "sess3")
    session_store.SESS_DIR.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(session_store, "TTL_SEC", 1)
    st.session_state.clear()
    store = session_store.SessionStore("run", defaults={"foo": 0}, persist_keys={"foo"})
    store.set("foo", 1)
    snap = session_store.SESS_DIR / f"{store.sid}_run.json"
    obj = json.loads(snap.read_text())
    obj["saved_at"] = time.time() - 2
    snap.write_text(json.dumps(obj))
    st.session_state.clear()
    store2 = session_store.SessionStore("run", defaults={"foo": 0}, persist_keys={"foo"})
    assert store2.get("foo") == 0
