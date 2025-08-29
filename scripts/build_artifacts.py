#!/usr/bin/env python3
"""Build deterministic Python artifacts and record hashes."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def get_source_date_epoch() -> int:
    """Return SOURCE_DATE_EPOCH from git or current time."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%ct"],
            capture_output=True,
            text=True,
            check=True,
        )
        return int(result.stdout.strip())
    except Exception:
        return int(time.time())


def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def clean(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    epoch = get_source_date_epoch()
    env = os.environ.copy()
    env.update(
        {
            "SOURCE_DATE_EPOCH": str(epoch),
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
            "LC_ALL": "C",
            "LANG": "C",
        }
    )
    os.environ.update(env)
    if hasattr(time, "tzset"):
        time.tzset()

    dist_dir = repo_root / "dist"
    build_dir = repo_root / "build"
    clean(dist_dir)
    clean(build_dir)

    try:
        subprocess.run(
            [sys.executable, "-m", "build", "--sdist", "--wheel"],
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as exc:
        print("build failed", file=sys.stderr)
        return exc.returncode

    artifacts = []
    for file in sorted(dist_dir.iterdir()):
        if file.is_file():
            artifacts.append(
                {
                    "path": f"dist/{file.name}",
                    "sha256": sha256sum(file),
                    "bytes": file.stat().st_size,
                }
            )

    reports_dir = repo_root / "reports" / "build"
    reports_dir.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    manifest = {
        "commit": commit,
        "source_date_epoch": epoch,
        "artifacts": artifacts,
    }
    (reports_dir / "build_manifest.json").write_text(json.dumps(manifest, indent=2))

    for art in artifacts:
        print(f"{art['path']}: sha256={art['sha256']} bytes={art['bytes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
