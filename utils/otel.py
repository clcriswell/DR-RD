from __future__ import annotations

import contextlib
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

_ENABLED = os.getenv("DRRD_OTEL_ENABLED", "1") == "1"
_FALLBACK_DIR = Path(".dr_rd/otel")
_FALLBACK_DIR.mkdir(parents=True, exist_ok=True)


def _maybe_import():
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        return trace, TracerProvider, Resource, BatchSpanProcessor, ConsoleSpanExporter, OTLPSpanExporter
    except Exception:
        return None


def trace_id_from_run(run_id: str) -> str:
    # 16 byte (32 hex) deterministic id
    return hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:32]


_trace, _TracerProvider, _Resource, _Batch, _Console, _OTLP = _maybe_import() or (None,) * 6
_tracer = None


def configure(service_name: str = "dr-rd") -> None:
    global _tracer
    if not _ENABLED or _trace is None:
        _tracer = None
        return
    if _tracer is not None:
        return
    provider = _TracerProvider(resource=_Resource.create({"service.name": service_name}))
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        provider.add_span_processor(_Batch(_OTLP(endpoint=endpoint)))
    if os.getenv("DRRD_OTEL_CONSOLE", "0") == "1" or not endpoint:
        provider.add_span_processor(_Batch(_Console()))
    _trace.set_tracer_provider(provider)
    _tracer = _trace.get_tracer(service_name)


@contextlib.contextmanager
def start_span(
    name: str,
    *,
    attrs: Optional[Dict[str, Any]] = None,
    run_id: str | None = None,
) -> Iterator[Any]:
    """
    If OTel available → real span. Else write a fallback span record to JSONL.
    Yields a small handle with .set_attribute(), .add_event(), .record_exception(), .get_span_context()
    """
    if _ENABLED and _tracer is not None:
        with _tracer.start_as_current_span(name) as span:
            if attrs:
                for k, v in attrs.items():
                    span.set_attribute(k, v)
            try:
                yield span
            except Exception as exc:  # pragma: no cover - defensive
                span.record_exception(exc)
                span.set_attribute("error", True)
                raise
    else:
        start = time.time()
        rec: Dict[str, Any] = {"name": name, "attrs": attrs or {}, "run_id": run_id, "t0": start}
        try:
            yield _FallbackSpan(rec)
        except Exception as exc:  # pragma: no cover - defensive
            rec["error"] = True
            rec["exc"] = str(exc)
            raise
        finally:
            rec["t1"] = time.time()
            (_FALLBACK_DIR / "spans.jsonl").open("a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")


@dataclass
class _FallbackSpan:
    _rec: Dict[str, Any]

    def set_attribute(self, k: str, v: Any) -> None:
        self._rec.setdefault("attrs", {})[k] = v

    def add_event(self, name: str, attrs: Optional[Dict[str, Any]] = None) -> None:
        ev = {"name": name, "attrs": attrs or {}, "t": time.time()}
        self._rec.setdefault("events", []).append(ev)

    def record_exception(self, exc: Exception) -> None:
        self._rec["exc"] = str(exc)

    def get_span_context(self) -> None:
        return None


def current_ids() -> Dict[str, str] | None:
    if _trace is None or _tracer is None:
        return None
    try:
        span = _trace.get_current_span()
        ctx = span.get_span_context()
        return {
            "trace_id": format(ctx.trace_id, "032x"),
            "span_id": format(ctx.span_id, "016x"),
        }
    except Exception:
        return None
