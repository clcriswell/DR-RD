from __future__ import annotations

import csv
import json
import traceback
from pathlib import Path
from threading import Lock
from typing import Any, Callable, List, Optional
from time import time

from pydantic import BaseModel


class APICallRecord(BaseModel):
    ts_start: float
    ts_end: float
    run_id: str
    task_id: str
    agent: str
    api_name: str
    endpoint: str
    params: dict[str, Any] | None = None
    prompt_text: str = ""
    response_text: str = ""
    status_code: int | None = None
    error: bool = False
    exception: str | None = None
    traceback: str | None = None


class APICallLogger:
    """Collect and persist API call records for a run."""

    def __init__(self, run_id: str, artifact_dir: Path, enabled: bool = True) -> None:
        self.run_id = run_id
        self.artifact_dir = artifact_dir
        self.enabled = enabled
        self._records: List[APICallRecord] = []
        self._lock = Lock()

    def log(self, record: APICallRecord) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._records.append(record)

    def flush(self) -> None:
        if not self.enabled:
            return
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        if not self._records:
            return
        jsonl_path = self.artifact_dir / "api_calls.jsonl"
        with jsonl_path.open("w", encoding="utf-8") as fh:
            for rec in self._records:
                fh.write(rec.model_dump_json() + "\n")
        csv_path = self.artifact_dir / "api_calls.csv"
        fieldnames = list(APICallRecord.model_fields)
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for rec in self._records:
                writer.writerow(rec.model_dump())
        md_path = self.artifact_dir / "api_calls.md"
        with md_path.open("w", encoding="utf-8") as fh:
            fh.write("# API Call Log\n\n")
            fh.write(
                "This table shows truncated prompts and responses. "
                "See api_calls.jsonl or api_calls.csv for full data.\n\n"
            )
            fh.write("| ts_start | api_name | prompt_text | response_text |\n")
            fh.write("|---|---|---|---|\n")
            for rec in self._records:
                pr = (rec.prompt_text or "")[:80].replace("\n", " ")
                rr = (rec.response_text or "")[:80].replace("\n", " ")
                fh.write(f"| {rec.ts_start} | {rec.api_name} | {pr} | {rr} |\n")

    def close(self) -> None:
        self.flush()
        with self._lock:
            self._records.clear()


def instrumented_api_call(
    api_name: str,
    endpoint: str,
    params: dict[str, Any] | None,
    prompt_text: str,
    call: Callable[[], Any],
    *,
    task_id: str = "",
    agent: str = "",
) -> Any:
    """Execute ``call`` and log request/response to the global APICallLogger."""
    from . import loggers as _loggers

    logger = _loggers.get_api_call_logger()
    ts_start = time()
    error = False
    exc_txt: str | None = None
    tb_txt: str | None = None
    status_code: int | None = None
    response_text = ""
    try:
        resp = call()
        status_code = getattr(resp, "http_status", None)
        if hasattr(resp, "model_dump_json"):
            response_text = resp.model_dump_json()
        elif hasattr(resp, "json"):
            try:
                response_text = json.dumps(resp.json())
            except Exception:
                response_text = str(resp)
        else:
            response_text = str(resp)
        return resp
    except Exception as e:
        error = True
        exc_txt = repr(e)
        tb_txt = traceback.format_exc()
        raise
    finally:
        ts_end = time()
        if logger is not None:
            record = APICallRecord(
                ts_start=ts_start,
                ts_end=ts_end,
                run_id=logger.run_id,
                task_id=task_id,
                agent=agent,
                api_name=api_name,
                endpoint=endpoint,
                params=params or {},
                prompt_text=prompt_text,
                response_text=response_text if not error else "",
                status_code=status_code,
                error=error,
                exception=exc_txt,
                traceback=tb_txt,
            )
            logger.log(record)
