from __future__ import annotations

"""Aggregate evaluation results into scoreboards."""

from typing import List, Dict, Any
import csv
from pathlib import Path
import statistics


def write_scoreboard(out_dir: Path, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "scoreboard.csv"
    fields = ["id", "tags", "status", "heuristic", "llm", "final", "tokens", "cost_usd", "duration_s", "run_id"]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k) for k in fields})
    md_path = out_dir / "scoreboard.md"
    pass_rate = 0.0
    mean_final = 0.0
    if rows:
        finals = [r["final"] for r in rows]
        mean_final = statistics.mean(finals)
        pass_rate = sum(1 for v in finals if v >= 0.7) / len(finals)
    with md_path.open("w", encoding="utf-8") as f:
        f.write("| id | tags | status | heuristic | llm | final | tokens | cost_usd | duration_s | run_id |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
        for r in rows:
            f.write(
                f"| {r['id']} | {','.join(r.get('tags', []))} | {r['status']} | {r['heuristic']:.3f} | "
                f"{r['llm'] if r['llm'] is not None else ''} | {r['final']:.3f} | {r['tokens']} | {r['cost_usd']:.4f} | {r['duration_s']:.2f} | {r['run_id']} |\n"
            )
        f.write("\n")
        f.write(f"Mean final: {mean_final:.3f}\n\n")
        f.write(f"Pass rate@0.7: {pass_rate:.1%}\n\n")
        top = sorted(rows, key=lambda r: r['final'], reverse=True)[:5]
        bottom = sorted(rows, key=lambda r: r['final'])[:5]
        if top:
            f.write("Top 5:\n")
            for r in top:
                f.write(f"- {r['id']} {r['final']:.3f}\n")
            f.write("\n")
        if bottom:
            f.write("Bottom 5:\n")
            for r in bottom:
                f.write(f"- {r['id']} {r['final']:.3f}\n")
            f.write("\n")
    return {"csv": str(csv_path), "md": str(md_path), "pass_rate": pass_rate, "mean_final": mean_final}
