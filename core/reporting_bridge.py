from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from dr_rd.kb import store
from dr_rd.kb.models import KBRecord, KBSource
from dr_rd.reporting import compose
from dr_rd.reporting.exporters import to_html, to_markdown


def _coerce_inputs(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, list):
        return {"items": list(value)}
    if value is None:
        return {}
    return {"value": value}


def kb_ingest(agent_role: str, task: Dict, output_json: Dict, route_meta: Dict, spans: Iterable[Dict]) -> None:
    """Persist agent output into the KB if enabled."""
    record = {
        "id": "",
        "run_id": route_meta.get("run_id", ""),
        "agent_role": agent_role,
        "task_title": task.get("title", ""),
        "task_desc": task.get("description", ""),
        "inputs": _coerce_inputs(task.get("inputs")),
        "output_json": output_json,
        "sources": output_json.get("sources", []),
        "ts": route_meta.get("ts", 0.0),
        "tags": route_meta.get("tags", []),
        "metrics": route_meta.get("metrics", {}),
        "provenance_span_ids": [s.get("id", "") for s in spans or []],
    }
    try:
        rec = KBRecord(**record)
        store.add(rec)
    except Exception:
        pass


def compose_and_export_report(plan_path: str, agents_jsonl: str, synth_path: str, out_dir: str) -> Dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(plan_path, "r", encoding="utf-8") as fh:
        plan = json.load(fh)
    agents = []
    with open(agents_jsonl, "r", encoding="utf-8") as fh:
        for line in fh:
            agents.append(json.loads(line))
    with open(synth_path, "r", encoding="utf-8") as fh:
        synth = json.load(fh)
    report = compose(plan, {"agents": agents, "synth": synth})
    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out / "report.md").write_text(to_markdown(report), encoding="utf-8")
    (out / "report.html").write_text(to_html(report), encoding="utf-8")
    return report
