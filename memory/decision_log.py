import json
import os
import datetime


def _path(project_id: str):
    os.makedirs("memory/decision_log", exist_ok=True)
    return f"memory/decision_log/{project_id}.jsonl"


def log_decision(project_id: str, step: str, data: dict):
    rec = {"t": datetime.datetime.utcnow().isoformat(), "step": step, "data": data}
    with open(_path(project_id), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
