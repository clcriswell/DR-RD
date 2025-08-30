from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Mapping

import core.orchestrator as orch
from utils import telemetry
from utils.cli import exit_code, load_config, print_summary
from utils.env_snapshot import capture_env
from utils.paths import ensure_run_dirs, write_text
from utils.run_config_io import to_lockfile
from utils.run_id import new_run_id
from utils.run_reproduce import to_orchestrator_kwargs
from utils.runs import complete_run_meta, create_run_meta, load_run_meta


def run(
    cfg: Mapping,
    *,
    run_id: str | None = None,
    out_dir: str | None = None,
    deadline_sec: float | None = None,
    telemetry_enabled: bool = True,
    budget_usd: float | None = None,
    max_tokens: int | None = None,
) -> tuple[Mapping, Mapping | None]:
    """Execute a single run and return metadata and totals."""
    from utils import paths as paths_mod

    if out_dir:
        paths_mod.RUNS_ROOT = Path(out_dir)
    rid = run_id or new_run_id()
    cfg = dict(cfg)
    if budget_usd is not None:
        cfg["budget_limit_usd"] = float(budget_usd)
        cfg["enforce_budget"] = True
    if max_tokens is not None:
        cfg["max_tokens"] = int(max_tokens)
        cfg["enforce_budget"] = True

    ensure_run_dirs(rid)
    locked = to_lockfile(cfg)
    write_text(rid, "run_config", "lock.json", json.dumps(locked))
    write_text(rid, "env", "snapshot.json", json.dumps(capture_env()))
    create_run_meta(rid, mode=cfg.get("mode", "standard"), idea_preview=cfg.get("idea", "")[:120])
    if telemetry_enabled:
        telemetry.log_event(
            {"event": "run_created", "run_id": rid, "mode": cfg.get("mode", "standard")}
        )
    kwargs = to_orchestrator_kwargs(locked)
    deadline_ts = time.time() + float(deadline_sec) if deadline_sec else None
    status = "error"
    start = time.time()
    try:
        tasks = orch.generate_plan(kwargs["idea"], deadline_ts=deadline_ts)
        answers = orch.execute_plan(kwargs["idea"], tasks, deadline_ts=deadline_ts)
        orch.compose_final_proposal(kwargs["idea"], answers)
        status = "success"
    except TimeoutError:
        status = "timeout"
    except RuntimeError:
        status = "cancelled"
    except Exception:
        status = "error"
    complete_run_meta(rid, status=status)
    if telemetry_enabled:
        telemetry.log_event({"event": "run_completed", "run_id": rid, "status": status})
    meta = load_run_meta(rid) or {
        "run_id": rid,
        "status": status,
        "started_at": int(start),
        "completed_at": int(time.time()),
    }
    return meta, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a DR RD pipeline headlessly")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--config", help="Path to JSON config")
    group.add_argument("--lockfile", help="Path to run_config.lock.json")
    parser.add_argument("--profile", help="Apply named profile first")
    parser.add_argument("--mode", help="Override run mode")
    parser.add_argument("--deadline-sec", type=float, default=None)
    parser.add_argument("--budget-usd", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--run-id", help="Explicit run_id")
    parser.add_argument("--out-dir", default=".dr_rd/runs")
    parser.add_argument("--no-telemetry", action="store_true")
    args = parser.parse_args(argv)

    cfg = load_config(args.config, args.lockfile, args.profile)
    if args.mode:
        cfg = dict(cfg)
        cfg["mode"] = args.mode
    meta, totals = run(
        cfg,
        run_id=args.run_id,
        out_dir=args.out_dir,
        deadline_sec=args.deadline_sec,
        telemetry_enabled=not args.no_telemetry,
        budget_usd=args.budget_usd,
        max_tokens=args.max_tokens,
    )
    print_summary(meta, totals, profile=args.profile)
    return exit_code(meta.get("status", "error"))


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
