import datetime
import json
import os
import socket
from pathlib import Path
from typing import Any, Dict, List


class Exporter:
    def write(self, event: Dict[str, Any]) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class FileExporter(Exporter):
    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self) -> Path:
        day = datetime.date.today().strftime("%Y%m%d")
        return self.log_dir / f"{day}.jsonl"

    def write(self, event: Dict[str, Any]) -> None:
        path = self._file_path()
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")


class StatsDExporter(Exporter):
    def __init__(self, host: str, port: int = 8125) -> None:
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def write(self, event: Dict[str, Any]) -> None:  # pragma: no cover - best effort
        name = event.get("name")
        val = event.get("value", 0)
        metric_type = event.get("type", "gauge")
        if metric_type == "counter":
            payload = f"{name}:{val}|c"
        elif metric_type == "histogram":
            payload = f"{name}:{val}|ms"
        else:
            payload = f"{name}:{val}|g"
        try:
            self.sock.sendto(payload.encode(), self.addr)
        except Exception:
            pass


class OTLPExporter(Exporter):
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint

    def write(self, event: Dict[str, Any]) -> None:  # pragma: no cover - placeholder
        # A full OTLP implementation is out of scope; this is a stub.
        pass


def get_exporters() -> List[Exporter]:
    exporters: List[Exporter] = []
    log_dir = Path(os.getenv("TELEMETRY_LOG_DIR", ".dr_rd/telemetry"))
    exporters.append(FileExporter(log_dir))
    statsd_host = os.getenv("STATSD_HOST")
    if statsd_host:
        try:
            exporters.append(StatsDExporter(statsd_host))
        except Exception:
            pass
    otlp = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp:
        exporters.append(OTLPExporter(otlp))
    return exporters
