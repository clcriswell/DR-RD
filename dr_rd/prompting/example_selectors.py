from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import yaml

from dr_rd.cache.memo import MemoCache
from dr_rd.examples import catalog
from dr_rd.kb import store

CONFIG_PATH = Path("config/reporting.yaml")
CONFIG = yaml.safe_load(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}

_memo = MemoCache(ttl=60.0)


def score_candidates(role: str, task_sig: str, provider: str, k_hint: int, max_tokens: int) -> List[Dict]:
    """Return scored and deduped example candidates."""

    def builder() -> List[Dict]:
        items = catalog.fetch(role, k_hint * 2)
        try:
            kb_items = [rec.output_json for rec in store.query({"agent_role": role}, limit=k_hint * 2)]
            items.extend(kb_items)
        except Exception:
            pass
        latest_ts = max([c.get("ts", 0) for c in items] or [0]) or 1
        scored: List[Dict] = []
        for c in items:
            score = c.get("quality_score", 0.0)
            recency = c.get("ts", 0) / latest_ts
            text = json.dumps(c.get("task", "")) + json.dumps(c.get("input", ""))
            lexical = 1.0 if task_sig and task_sig.lower() in text.lower() else 0.0
            c = dict(c)  # copy
            c["_score"] = score * (1 + recency * CONFIG.get("EXAMPLE_RECENCY_WEIGHT", 0)) + lexical
            scored.append(c)
        scored.sort(key=lambda x: x.get("_score", 0), reverse=True)
        seen = set()
        out: List[Dict] = []
        for c in scored:
            sig = c.get("task") or c.get("id")
            if sig in seen:
                continue
            seen.add(sig)
            out.append(c)
            if len(out) >= k_hint:
                break
        return out

    key = (role, task_sig, provider, k_hint, max_tokens)
    return _memo.get_or_set(key, builder)


def pack_for_provider(cands: List[Dict], provider: str, json_mode: bool) -> Dict:
    messages: List[Dict] = []
    for c in cands:
        inp = c.get("input") or c.get("task") or ""
        out = c.get("output") or {}
        if json_mode and isinstance(out, dict):
            out = {k: v for k, v in out.items() if k not in ("reasoning", "cot", "thought")}
            out_text = json.dumps(out)
        else:
            out_text = out if isinstance(out, str) else json.dumps(out)
        if provider == "openai":
            if not messages:
                messages.append({"role": "system", "content": "return only JSON"})
            messages.append({"role": "user", "content": inp})
            messages.append({"role": "assistant", "content": out_text})
        elif provider == "anthropic":
            if not messages:
                messages.append({"role": "system", "content": "return JSON"})
            messages.append({"role": "user", "content": inp})
            messages.append({"role": "assistant", "content": out_text})
        else:  # gemini
            messages.append({"name": "example", "args": inp, "response": out_text})
    tokens_est = sum(len(json.dumps(m)) for m in messages) // 4
    return {"provider": provider, "messages": messages, "summary": {"n": len(cands), "tokens_est": tokens_est}}
