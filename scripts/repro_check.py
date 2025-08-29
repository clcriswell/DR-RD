#!/usr/bin/env python3
"""Check build reproducibility by building twice and comparing artifacts."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path


def get_source_date_epoch() -> int:
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


def copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns("dist", "build", "reports", ".git"),
        dirs_exist_ok=True,
    )


def build(dir_path: Path, env: dict[str, str]) -> dict[str, dict[str, int | str]]:
    subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--wheel"],
        cwd=dir_path,
        env=env,
        check=True,
    )
    dist = dir_path / "dist"
    artifacts: dict[str, dict[str, int | str]] = {}
    for file in sorted(dist.iterdir()):
        if file.is_file():
            artifacts[file.name] = {
                "sha256": sha256sum(file),
                "bytes": file.stat().st_size,
            }
    return artifacts


def diff_members(p1: Path, p2: Path) -> dict[str, list[str]]:
    if p1.suffix == ".whl" or p1.suffix.endswith(".zip"):
        with zipfile.ZipFile(p1) as z1, zipfile.ZipFile(p2) as z2:
            m1 = {n: hashlib.sha256(z1.read(n)).hexdigest() for n in sorted(z1.namelist()) if not n.endswith("/")}
            m2 = {n: hashlib.sha256(z2.read(n)).hexdigest() for n in sorted(z2.namelist()) if not n.endswith("/")}
    else:
        with tarfile.open(p1, "r:*") as t1, tarfile.open(p2, "r:*") as t2:
            m1 = {}
            for m in t1.getmembers():
                if m.isfile():
                    f = t1.extractfile(m)
                    if f:
                        m1[m.name] = hashlib.sha256(f.read()).hexdigest()
            m2 = {}
            for m in t2.getmembers():
                if m.isfile():
                    f = t2.extractfile(m)
                    if f:
                        m2[m.name] = hashlib.sha256(f.read()).hexdigest()
    missing1 = sorted(set(m2) - set(m1))
    missing2 = sorted(set(m1) - set(m2))
    differing = sorted(name for name in set(m1) & set(m2) if m1[name] != m2[name])
    return {
        "missing_in_build1": missing1,
        "missing_in_build2": missing2,
        "differing": differing,
    }


def main() -> int:
    repo_root = Path.cwd()
    reports_dir = repo_root / "reports" / "build"
    reports_dir.mkdir(parents=True, exist_ok=True)

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

    report: dict[str, object]
    try:
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            copy_tree(repo_root, Path(d1))
            copy_tree(repo_root, Path(d2))
            arts1 = build(Path(d1), env)
            arts2 = build(Path(d2), env)

            artifacts_report = []
            deterministic = arts1 == arts2
            normalized_pass = True
            if deterministic:
                for name, info in sorted(arts1.items()):
                    artifacts_report.append(
                        {
                            "path": f"dist/{name}",
                            "sha256": info["sha256"],
                            "bytes": info["bytes"],
                        }
                    )
                report = {"deterministic": True, "artifacts": artifacts_report}
            else:
                all_names = sorted(set(arts1) | set(arts2))
                for name in all_names:
                    entry = {"path": f"dist/{name}"}
                    a1 = arts1.get(name)
                    a2 = arts2.get(name)
                    if a1:
                        entry["build1"] = a1
                    if a2:
                        entry["build2"] = a2
                    if a1 and a2 and a1["sha256"] == a2["sha256"]:
                        entry["matches"] = True
                    else:
                        entry["matches"] = False
                        if a1 and a2:
                            diff = diff_members(Path(d1) / "dist" / name, Path(d2) / "dist" / name)
                            entry["member_diffs"] = diff
                            if (
                                diff["missing_in_build1"]
                                or diff["missing_in_build2"]
                                or diff["differing"]
                            ):
                                normalized_pass = False
                        else:
                            normalized_pass = False
                    artifacts_report.append(entry)
                report = {
                    "deterministic": False,
                    "normalized_pass": normalized_pass,
                    "artifacts": artifacts_report,
                }
    except subprocess.CalledProcessError as exc:
        report = {"deterministic": False, "error": f"build failed: {exc}"}
        print("reproducibility check failed: build error")

    (reports_dir / "repro_report.json").write_text(json.dumps(report, indent=2))
    if report.get("deterministic"):
        print("reproducible build: hashes match")
    else:
        print("reproducible build: mismatch")
        if report.get("normalized_pass"):
            print("normalized contents match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
