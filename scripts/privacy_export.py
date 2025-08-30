import argparse
import json
import shutil
from pathlib import Path

from utils.redaction import redact_dict


def export_run(run_id: str, out_dir: Path) -> dict[str, int]:
    runs_root = Path("runs")
    run_src = runs_root / run_id
    if not run_src.exists():
        raise FileNotFoundError(run_src)

    out_dir.mkdir(parents=True, exist_ok=True)
    run_dst = out_dir / "runs" / run_id
    if run_dst.exists():
        shutil.rmtree(run_dst)
    shutil.copytree(run_src, run_dst)

    tele_root = Path(".dr_rd/telemetry")
    events = []
    if tele_root.exists():
        for p in tele_root.glob("events-*.jsonl"):
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    if ev.get("run_id") == run_id:
                        events.append(redact_dict(ev))
    if events:
        tele_out = out_dir / "telemetry.jsonl"
        with tele_out.open("w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    return {"files": sum(1 for _ in run_dst.rglob("*")), "events": len(events)}


def main() -> None:
    ap = argparse.ArgumentParser(description="Export run data with redaction")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    summary = export_run(args.run_id, Path(args.out))
    print(f"exported {summary['files']} files and {summary['events']} events")


if __name__ == "__main__":
    main()
