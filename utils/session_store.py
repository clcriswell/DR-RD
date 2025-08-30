from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import json, os, time, uuid
from typing import Any, Dict, Iterable, Mapping, Optional

SESS_DIR = Path(".dr_rd/session")
SESS_DIR.mkdir(parents=True, exist_ok=True)
TTL_SEC = int(os.getenv("SESSION_TTL_SEC", 7 * 24 * 3600))  # 7 days

@dataclass
class SessionStore:
    namespace: str
    defaults: Mapping[str, Any] = field(default_factory=dict)
    persist_keys: Iterable[str] = field(default_factory=tuple)

    def __post_init__(self):
        import streamlit as st
        # One stable id per browser tab
        if "session_id" not in st.session_state:
            st.session_state["session_id"] = uuid.uuid4().hex
        self.sid = st.session_state["session_id"]
        # Namespaced bucket
        key = self._nskey()
        if key not in st.session_state:
            st.session_state[key] = dict(self.defaults)
            # merge from saved snapshot (if present)
            snap = self._load_snapshot()
            if snap:
                st.session_state[key].update({k: v for k, v in snap.items() if k in self.defaults})
        self._touch()

    # ----- public API -----
    def get(self, k: str, default: Any = None) -> Any:
        import streamlit as st
        return st.session_state[self._nskey()].get(k, self.defaults.get(k, default))

    def set(self, k: str, v: Any) -> None:
        import streamlit as st
        st.session_state[self._nskey()][k] = v
        if k in set(self.persist_keys):
            self._save_snapshot()

    def as_dict(self) -> Dict[str, Any]:
        import streamlit as st
        return dict(st.session_state[self._nskey()])

    def seed(self, init: Mapping[str, Any]) -> None:
        """Idempotent merge of initial values (used once on app load)."""
        import streamlit as st
        bucket = st.session_state[self._nskey()]
        for k, v in init.items():
            if k in self.defaults and bucket.get(k) is None:
                bucket[k] = v
        self._save_snapshot()

    def clear(self, keys: Optional[Iterable[str]] = None) -> None:
        import streamlit as st
        bucket = st.session_state[self._nskey()]
        if keys is None:
            keys = list(bucket.keys())
        for k in keys:
            bucket.pop(k, None)
        for k, v in self.defaults.items():
            bucket.setdefault(k, v)
        self._save_snapshot()

    # ----- persistence -----
    def _snap_path(self) -> Path:
        return SESS_DIR / f"{self.sid}_{self.namespace}.json"

    def _save_snapshot(self) -> None:
        p = self._snap_path()
        data = {k: v for k, v in self.as_dict().items() if k in set(self.persist_keys)}
        p.write_text(json.dumps({"saved_at": time.time(), "data": data}, ensure_ascii=False), encoding="utf-8")

    def _load_snapshot(self) -> Optional[Dict[str, Any]]:
        p = self._snap_path()
        if not p.exists():
            return None
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if time.time() - float(obj.get("saved_at", 0)) > TTL_SEC:
                return None
            return obj.get("data") or {}
        except Exception:
            return None

    def _touch(self) -> None:
        # update a heartbeat file for cleanup bookkeeping
        (SESS_DIR / f"{self.sid}.touch").write_text(str(time.time()), encoding="utf-8")

    def _nskey(self) -> str:
        return f"_ns_{self.namespace}"

def get_session_id() -> str:
    import streamlit as st
    return str(st.session_state.get("session_id", ""))

def cleanup_expired(ttl_sec: int = TTL_SEC) -> int:
    """Delete old snapshots and heartbeats. Return files removed."""
    removed = 0
    now = time.time()
    for p in SESS_DIR.glob("*.json"):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if now - float(obj.get("saved_at", 0)) > ttl_sec:
                p.unlink(missing_ok=True); removed += 1
        except Exception:
            p.unlink(missing_ok=True); removed += 1
    for t in SESS_DIR.glob("*.touch"):
        try:
            ts = float(t.read_text(encoding="utf-8"))
            if now - ts > ttl_sec:
                t.unlink(missing_ok=True); removed += 1
        except Exception:
            t.unlink(missing_ok=True); removed += 1
    return removed


def init_stores() -> tuple[SessionStore, SessionStore]:
    import streamlit as st
    from .query_params import decode_config, view_state_from_params
    from .run_config import defaults as run_defaults

    run_store = SessionStore(
        "run",
        defaults=run_defaults().__dict__ if hasattr(run_defaults(), "__dict__") else {},
        persist_keys={"idea", "mode", "knowledge_sources", "budget_limit_usd", "max_tokens"},
    )
    if not st.session_state.get("_qp_seeded", False):
        decoded = decode_config(dict(st.query_params))
        run_store.seed(decoded)
        st.session_state["_qp_seeded"] = True

    view_store = SessionStore(
        "view",
        defaults={"trace_view": "summary", "trace_query": "", "palette_open": False},
        persist_keys={"trace_view", "trace_query"},
    )
    if not st.session_state.get("_view_seeded", False):
        vs = view_state_from_params(dict(st.query_params))
        view_store.set("trace_view", vs["trace_view"])
        view_store.set("trace_query", vs["trace_query"])
        st.session_state["_view_seeded"] = True

    return run_store, view_store
