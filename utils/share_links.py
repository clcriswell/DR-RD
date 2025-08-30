import base64
import json
import hmac
import hashlib
import time
import urllib.parse
from typing import Dict, List, Optional, Tuple

from .secrets import require


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _b64ud(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def sign(run_id: str, *, scopes: List[str], ttl_sec: int, extra: Optional[Dict] = None) -> str:
    secret = require("SHARE_SECRET")
    now = int(time.time())
    payload = {"rid": run_id, "scopes": scopes, "nbf": now - 60, "exp": now + int(ttl_sec)}
    if extra:
        payload.update(extra)
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return f"{_b64u(body)}.{_b64u(sig)}"

def verify(token: str) -> Dict:
    secret = require("SHARE_SECRET")
    try:
        body_b64, sig_b64 = token.split(".", 1)
    except ValueError:
        raise ValueError("bad_format")
    body = _b64ud(body_b64)
    expect = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    if not hmac.compare_digest(expect, _b64ud(sig_b64)):
        raise ValueError("bad_sig")
    obj = json.loads(body)
    now = int(time.time())
    if obj.get("nbf", 0) > now:
        raise ValueError("nbf")
    if obj.get("exp", 0) < now:
        raise ValueError("exp")
    obj["scopes"] = [s for s in obj.get("scopes", []) if s in {"trace", "reports", "artifacts"}]
    return obj

def make_link(base_url: str, run_id: str, *, scopes: List[str], ttl_sec: int, view: str = "trace") -> str:
    tok = sign(run_id, scopes=scopes, ttl_sec=ttl_sec)
    qp = {"view": view, "run_id": run_id, "share": tok}
    return f"{base_url}/?{urllib.parse.urlencode(qp)}"

def viewer_from_query(params: Dict[str, str]) -> Tuple[bool, Dict]:
    tok = params.get("share")
    if not tok:
        return False, {}
    try:
        obj = verify(tok)
        return True, obj
    except ValueError as e:
        return False, {"error": str(e)}
