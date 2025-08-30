"""Survey storage helpers."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import streamlit as st

from .cache import cached_data
from .redaction import redact_text

SURVEYS_PATH = Path(".dr_rd/telemetry/surveys.jsonl")
SURVEYS_PATH.parent.mkdir(parents=True, exist_ok=True)

try:  # pragma: no cover - secrets may not exist
    _FF_FIRESTORE = bool(st.secrets.get("gcp_service_account"))
except Exception:  # StreamlitSecretNotFoundError when no secrets file
    _FF_FIRESTORE = False


def _write_record(record: dict) -> None:
    with SURVEYS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    if _FF_FIRESTORE:
        threading.Thread(target=_mirror_to_firestore, args=(record,), daemon=True).start()


def _mirror_to_firestore(record: dict) -> None:  # pragma: no cover - best effort
    try:
        from google.cloud import firestore  # type: ignore
        from google.oauth2 import service_account  # type: ignore

        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        client = firestore.Client(credentials=creds, project=creds.project_id)
        client.collection("dr_rd_surveys").add(record)
    except Exception:
        pass


def save_sus(run_id: str, answers: dict[str, int], total: int, comment: str | None) -> None:
    try:
        from utils.consent import allowed_surveys

        if not allowed_surveys():
            return
    except Exception:
        pass
    clean = redact_text(comment or "")[:1000]
    record = {
        "ts": time.time(),
        "run_id": run_id,
        "instrument": "SUS",
        "version": 1,
        "answers": answers,
        "total": total,
        "comment": clean,
    }
    _write_record(record)


def save_seq(run_id: str, score: int, comment: str | None) -> None:
    try:
        from utils.consent import allowed_surveys

        if not allowed_surveys():
            return
    except Exception:
        pass
    clean = redact_text(comment or "")[:1000]
    record = {
        "ts": time.time(),
        "run_id": run_id,
        "instrument": "SEQ",
        "version": 1,
        "answers": {"score": score},
        "comment": clean,
    }
    _write_record(record)


@cached_data(ttl=30)
def load_recent(n: int = 500) -> list[dict]:
    try:
        from utils.consent import allowed_surveys

        if not allowed_surveys():
            return []
    except Exception:
        pass
    if not SURVEYS_PATH.exists():
        return []
    with SURVEYS_PATH.open("r", encoding="utf-8") as f:
        lines = f.readlines()[-n:]
    return [json.loads(line) for line in lines]


def compute_aggregates(records: list[dict]) -> dict[str, float]:
    try:
        from utils.consent import allowed_surveys

        if not allowed_surveys():
            return {
                "sus_count": 0,
                "sus_mean": 0.0,
                "sus_7_day_mean": 0.0,
                "seq_count": 0,
                "seq_mean": 0.0,
                "seq_7_day_mean": 0.0,
            }
    except Exception:
        pass
    now = time.time()
    cutoff = now - 7 * 24 * 60 * 60
    sus_scores = [r.get("total", 0) for r in records if r.get("instrument") == "SUS"]
    sus_recent = [
        r.get("total", 0)
        for r in records
        if r.get("instrument") == "SUS" and r.get("ts", 0) >= cutoff
    ]
    seq_scores = [
        r.get("answers", {}).get("score") for r in records if r.get("instrument") == "SEQ"
    ]
    seq_recent = [
        r.get("answers", {}).get("score")
        for r in records
        if r.get("instrument") == "SEQ" and r.get("ts", 0) >= cutoff
    ]

    def _mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    return {
        "sus_count": len(sus_scores),
        "sus_mean": _mean(sus_scores),
        "sus_7_day_mean": _mean(sus_recent),
        "seq_count": len(seq_scores),
        "seq_mean": _mean(seq_scores),
        "seq_7_day_mean": _mean(seq_recent),
    }
