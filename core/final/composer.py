from typing import Dict, Any, List
import re
import json
import os
import csv
import zipfile
import pathlib

REQUIRED_SECTIONS = [
    "Executive Summary",
    "Problem & Value",
    "Research Findings",
    "Risks & Unknowns",
    "Architecture & Interfaces",
    "Regulatory & Compliance",
    "IP & Prior Art",
    "Market & GTM",
    "Cost Overview",
    "Next Steps",
]

def _ensure_sections(text: str) -> str:
    out = text
    for h in REQUIRED_SECTIONS:
        if re.search(rf'^##\s+{re.escape(h)}\b', out, re.M) is None:
            out += f"\n\n## {h}\n"
    return out


def write_final_bundle(
    slug: str,
    final_markdown: str,
    appendices: Dict[str, str],
    trace_rows: List[Dict[str, str]],
) -> Dict[str, str]:
    base = pathlib.Path(f"audits/{slug}/final")
    base.mkdir(parents=True, exist_ok=True)
    # final report
    report_path = base / "final_report.md"
    report_path.write_text(_ensure_sections(final_markdown), encoding="utf-8")
    # appendices map
    (base / "appendices_map.json").write_text(
        json.dumps(appendices, indent=2), encoding="utf-8"
    )
    # traceability matrix
    trace_path = base / "traceability_matrix.csv"
    if trace_rows:
        with open(trace_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(trace_rows[0].keys()))
            w.writeheader()
            for r in trace_rows:
                w.writerow(r)
    # zip bundle
    bundle = base / "final_bundle.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(report_path, arcname="final_report.md")
        z.write(base / "appendices_map.json", arcname="appendices_map.json")
        if trace_rows:
            z.write(trace_path, arcname="traceability_matrix.csv")
        # include referenced appendix files if they exist
        for name, p in appendices.items():
            if p and os.path.exists(p):
                z.write(p, arcname=f"appendices/{os.path.basename(p)}")
    return {
        "report": str(report_path),
        "appendices_map": str(base / "appendices_map.json"),
        "traceability": str(trace_path) if trace_rows else "",
        "bundle": str(bundle),
    }
