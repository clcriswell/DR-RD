from pathlib import Path
import json, time
from typing import Literal

STATE = Path('.dr_rd/circuits.json')
WINDOW_SEC = 60
THRESH_FAILS = 3

def _load() -> dict:
    try:
        return json.loads(STATE.read_text('utf-8'))
    except Exception:
        return {}

def _save(d: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')

def status(key: str) -> Literal['closed','open','half']:
    d = _load().get(key) or {}
    until = d.get('until', 0)
    if time.time() < until:
        return 'open'
    if d.get('half', False):
        return 'half'
    return 'closed'

def record_failure(key: str) -> str:
    d = _load()
    e = d.get(key, {'fails':0})
    e['fails'] = e.get('fails',0) + 1
    if e['fails'] >= THRESH_FAILS:
        e['until'] = time.time() + WINDOW_SEC
        e['half'] = False
        state = 'open'
    else:
        state = 'closed'
    d[key] = e
    _save(d)
    return state

def allow_half_open(key: str) -> bool:
    d = _load()
    e = d.get(key, {})
    if e.get('until',0) <= time.time():
        e['half'] = True
        d[key] = e
        _save(d)
        return True
    return False

def record_success(key: str) -> None:
    d = _load()
    d[key] = {'fails':0}
    _save(d)
