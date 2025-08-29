"""Offline demo flows for GTM kit."""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from dr_rd.connectors.commons import load_fixture, use_fixtures

SAMPLES = Path("samples")


def _apply_flags(flags: str | None) -> None:
    if not flags:
        return
    for item in flags.split(","):
        if "=" in item:
            k, v = item.split("=", 1)
            os.environ[k] = v


def _write_artifacts(out_dir: Path, name: str, data: Dict[str, Any], summary: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / f"{name}.json", "w") as f:
        json.dump(data, f, indent=2)
    with open(out_dir / f"{name}.md", "w") as f:
        f.write(summary)


def run_materials_tradeoff(out_dir: str, flags: str | None = None) -> None:
    _apply_flags(flags)
    tasks = [json.loads(l) for l in (SAMPLES / "tasks/materials_tradeoff.jsonl").open()]
    best = max(tasks, key=lambda x: x["yield"] / x["cost"])
    data = {"items": tasks, "best_material": best["material"]}
    summary = f"Best material: {best['material']}\n"
    _write_artifacts(Path(out_dir), "materials", data, summary)


def run_qa_check(out_dir: str, flags: str | None = None) -> None:
    _apply_flags(flags)
    tasks = [json.loads(l) for l in (SAMPLES / "tasks/qa_requirements.jsonl").open()]
    items = []
    for t in tasks:
        items.append({"requirement": t["requirement"], "tests": t["tests"], "passed": True})
    data = {"items": items}
    summary = "All QA checks passed\n"
    _write_artifacts(Path(out_dir), "qa", data, summary)


def run_finance_eval(out_dir: str, flags: str | None = None) -> None:
    _apply_flags(flags)
    tasks = [json.loads(l) for l in (SAMPLES / "tasks/finance_unit_econ.jsonl").open()]
    items = []
    for t in tasks:
        npv = t["value"] / (1 + t["discount_rate"])
        items.append({"line_item": t["line_item"], "npv": npv})
    data = {"items": items}
    summary = "NPV computed\n"
    _write_artifacts(Path(out_dir), "finance", data, summary)


def run_compliance_mock(out_dir: str, flags: str | None = None) -> None:
    _apply_flags(flags)
    regs = [json.loads(l) for l in (SAMPLES / "tasks/regulatory_mock.jsonl").open()]
    pats = [json.loads(l) for l in (SAMPLES / "tasks/patent_mock.jsonl").open()]
    sources = []
    if use_fixtures():
        cfr = load_fixture("cfr_lookup") or {"items": []}
        uspto = load_fixture("uspto_search_patents") or {"items": []}
        sources = [cfr.get("items", [{}])[0].get("url"), uspto.get("items", [{}])[0].get("url")]
    data = {
        "items": [{"regulation": regs[0]["cfr_ref"], "patent_query": pats[0]["query"], "sources": [s for s in sources if s]}]
    }
    summary = "Compliance mock complete\n"
    _write_artifacts(Path(out_dir), "compliance", data, summary)


def run_dynamic_role(out_dir: str, flags: str | None = None) -> None:
    _apply_flags(flags)
    data = {"result": "Dynamic spec executed"}
    summary = "Dynamic role run\n"
    _write_artifacts(Path(out_dir), "dynamic", data, summary)


FLOW_MAP = {
    "materials": run_materials_tradeoff,
    "qa": run_qa_check,
    "finance": run_finance_eval,
    "compliance": run_compliance_mock,
    "dynamic": run_dynamic_role,
}


def run_all(out_dir: str, flags: str | None = None) -> None:
    for name, fn in FLOW_MAP.items():
        fn(out_dir, flags)
