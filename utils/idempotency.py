import hashlib, json, time
from pathlib import Path
from typing import Any, Mapping, Optional

ROOT = Path('.dr_rd/cache/llm')
ROOT.mkdir(parents=True, exist_ok=True)

def canonical_payload(prompt: Mapping[str, Any]) -> bytes:
    return json.dumps(prompt, separators=(',',':'), sort_keys=True, ensure_ascii=False).encode('utf-8')

def key(provider: str, model: str, payload: Mapping[str, Any]) -> str:
    h = hashlib.sha256()
    h.update(provider.encode())
    h.update(b':')
    h.update(model.encode())
    h.update(canonical_payload(payload))
    return h.hexdigest()

def get(k: str, ttl_sec: Optional[int]=None) -> Optional[dict]:
    p = ROOT / f"{k}.json"
    if not p.exists():
        return None
    if ttl_sec is not None and (time.time() - p.stat().st_mtime) > ttl_sec:
        return None
    try:
        return json.loads(p.read_text('utf-8'))
    except Exception:
        return None

def put(k: str, resp: Mapping[str, Any]) -> None:
    p = ROOT / f"{k}.json"
    p.write_text(json.dumps(resp, ensure_ascii=False), encoding='utf-8')
