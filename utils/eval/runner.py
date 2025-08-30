from __future__ import annotations

"""Run evaluation datasets and collect artifacts."""

from typing import List, Dict, Any
import os
import time
import json
from pathlib import Path

import streamlit as st

from utils.run_id import new_run_id
from app.init import get_agents
from core.orchestrator import run_stream
from utils.telemetry import eval_started, eval_item_completed, eval_completed
from . import scoring, report

BASE_DIR = Path(".dr_rd/eval")


def _collect_events(events) -> tuple[str, Dict[str, Any], str]:
    text = ""
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0}
    status = "error"
    for ev in events:
        if ev.kind == "summary" and ev.phase == "synth":
            text = ev.text or ""
        elif ev.kind == "usage_delta" and ev.meta:
            meta = ev.meta
            usage["prompt_tokens"] += int(meta.get("prompt_tokens", 0))
            usage["completion_tokens"] += int(meta.get("completion_tokens", 0))
            usage["cost_usd"] += float(meta.get("cost_usd", 0.0))
        elif ev.kind == "done":
            status = "success"
        elif ev.kind == "error":
            status = "error"
    return text, usage, status


def run_eval(items: List[Dict[str, Any]], *, use_llm: bool = False, concurrency: int = 1, out_dir: str | None = None) -> Dict[str, Any]:
    if concurrency != 1:
        raise NotImplementedError("concurrency >1 not supported yet")
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_base = Path(out_dir) if out_dir else BASE_DIR / ts
    results_dir = out_base / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    eval_started(len(items), use_llm)
    rows = []
    for spec in items:
        start = time.time()
        run_id = new_run_id()
        st.session_state["budget_limit_usd"] = spec.get("limits", {}).get("budget_usd")
        st.session_state["max_tokens"] = spec.get("limits", {}).get("max_tokens")
        st.session_state["mode"] = spec.get("mode", "standard")
        if spec.get("seed") is not None:
            os.environ["DRRD_SEED"] = str(spec["seed"])
        else:
            os.environ.pop("DRRD_SEED", None)
        agents = get_agents()
        events = run_stream(spec["idea"], run_id=run_id, agents=agents)
        text, usage, status = _collect_events(events)
        duration = time.time() - start
        score = scoring.score_item(text, {"status": status, "usage": usage}, spec, use_llm=use_llm)
        row = {
            "id": spec["id"],
            "tags": spec.get("tags", []),
            "status": status,
            "heuristic": score["heuristic"],
            "llm": score["llm"],
            "final": score["final"],
            "tokens": usage["prompt_tokens"] + usage["completion_tokens"],
            "cost_usd": usage["cost_usd"],
            "duration_s": duration,
            "run_id": run_id,
            "flags": score["flags"],
        }
        rows.append(row)
        with (results_dir / f"{spec['id']}.json").open("w", encoding="utf-8") as f:
            json.dump({**row, "usage": usage}, f, ensure_ascii=False, indent=2)
        eval_item_completed(spec["id"], status, score["final"], run_id=run_id)
    summary = report.write_scoreboard(out_base, rows)
    eval_completed(len(items), summary["pass_rate"], summary["mean_final"])
    return {**summary, "rows": rows, "out_dir": str(out_base)}
