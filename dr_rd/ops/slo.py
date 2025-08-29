import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def load_events(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for p in paths:
        if not p.exists():
            continue
        with open(p, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def compute_slo(events: List[Dict[str, Any]], targets: Dict[str, Any]) -> Dict[str, Any]:
    runs_started = sum(e.get("value", 0) for e in events if e.get("name") == "runs_started")
    runs_succeeded = sum(e.get("value", 0) for e in events if e.get("name") == "runs_succeeded")
    runs_failed = sum(e.get("value", 0) for e in events if e.get("name") == "runs_failed")
    availability = 0.0
    if runs_started:
        availability = 100.0 * runs_succeeded / runs_started

    phase_lat: Dict[str, List[float]] = {}
    for e in events:
        if e.get("name") == "phase_latency_ms":
            phase = e.get("labels", {}).get("phase") or "unknown"
            phase_lat.setdefault(phase, []).append(float(e.get("value", 0.0)))
    latency_p95: Dict[str, float] = {}
    for phase, vals in phase_lat.items():
        if not vals:
            latency_p95[phase] = 0.0
        else:
            vals = sorted(vals)
            k = int(0.95 * (len(vals) - 1))
            latency_p95[phase] = vals[k]

    missing_citations = sum(
        e.get("value", 0) for e in events if e.get("name") == "citations_missing"
    )
    schema_fail = sum(
        e.get("value", 0) for e in events if e.get("name") == "schema_validation_failures"
    )
    quality = 100.0
    validity = 100.0
    if runs_started:
        quality = 100.0 * (1.0 - missing_citations / runs_started)
        validity = 100.0 * (1.0 - schema_fail / runs_started)

    sli_values = {
        "availability": availability,
        "latency_p95_ms": latency_p95,
        "quality": quality,
        "validity": validity,
    }

    budget_remaining: Dict[str, Any] = {}
    for key, target in targets.get("slos", {}).items():
        sli = sli_values.get(key)
        if isinstance(sli, (int, float)) and isinstance(target, (int, float)):
            budget_remaining[key] = {
                "target": target,
                "remaining": target - float(sli),
            }
    return {"sli_values": sli_values, "budget_remaining": budget_remaining}
