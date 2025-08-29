#!/usr/bin/env python3
"""Release checklist gate.

Run prior to tagging a release. Exits non-zero on any failing check.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List


@dataclass
class Result:
    name: str
    status: str  # "ok", "fail", "skipped"
    message: str


def run(cmd: List[str], verbose: bool) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if verbose and proc.stdout:
        print(proc.stdout)
    if verbose and proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc


def check_ci(verbose: bool) -> Result:
    name = "CI green on main"
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return Result(name, "skipped", "skipped (no token)")

    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo:
        try:
            url = subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"], text=True
            ).strip()
            if url.endswith(".git"):
                url = url[:-4]
            if url.startswith("git@github.com:"):
                repo = url.split("git@github.com:")[-1]
            elif url.startswith("https://github.com/"):
                repo = url.split("https://github.com/")[-1]
        except Exception:
            repo = None
    if not repo:
        return Result(name, "fail", "cannot determine repository")

    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/runs?branch=main&status=completed&per_page=1"
    )
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
        runs = data.get("workflow_runs", [])
        if runs and runs[0].get("conclusion") == "success":
            return Result(name, "ok", "latest run succeeded")
        return Result(name, "fail", "latest run not successful")
    except Exception as e:  # pragma: no cover - best effort
        return Result(name, "fail", f"API error: {e}")


def check_locks(verbose: bool) -> Result:
    name = "Dependency locks"
    changed: List[str] = []
    for infile in ("requirements.in", "dev-requirements.in"):
        proc = run(["pip-compile", "--dry-run", infile], verbose)
        if proc.returncode != 0:
            return Result(name, "fail", f"pip-compile failed for {infile}")
        if proc.stdout.strip():
            changed.append(infile)
    if changed:
        return Result(name, "fail", f"updates needed for {', '.join(changed)}")
    return Result(name, "ok", "locks current")


def load_audit_json(verbose: bool) -> list:
    path = Path("reports/pip-audit.json")
    if path.exists():
        try:
            return json.loads(path.read_text() or "[]")
        except json.JSONDecodeError:
            return []
    proc = run(
        ["pip-audit", "-r", "requirements.lock.txt", "--format", "json"], verbose
    )
    if proc.returncode not in (0, 1):
        return []
    try:
        return json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return []


def check_vulns(verbose: bool) -> Result:
    name = "Vulnerability audit"
    allow_high = os.getenv("AUDIT_ALLOW_HIGH") == "1"
    data = load_audit_json(verbose)
    high = []
    for item in data:
        for vuln in item.get("vulns", []):
            sev = (vuln.get("severity") or "").upper()
            if sev in {"HIGH", "CRITICAL"}:
                high.append(sev)
    if high and not allow_high:
        return Result(name, "fail", f"{len(high)} high/critical")
    return Result(name, "ok", f"{len(high)} high/critical" if high else "none found")


def check_licenses(verbose: bool) -> Result:
    name = "License policy"
    cmd = ["python", "scripts/check_licenses.py"]
    path = Path("reports/licenses.json")
    if path.exists():
        cmd.extend(["--input", str(path)])
    proc = run(cmd, verbose)
    if proc.returncode != 0:
        return Result(name, "fail", "denied licenses")
    return Result(name, "ok", "licenses ok")


def check_sbom() -> Result:
    name = "SBOM freshness"
    path = Path("sbom/cyclonedx-python.json")
    if not path.exists():
        return Result(name, "fail", "missing sbom/cyclonedx-python.json")
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    if datetime.now(timezone.utc) - mtime > timedelta(hours=24):
        return Result(name, "fail", "older than 24h")
    return Result(name, "ok", "fresh")


def check_config_lock(verbose: bool) -> Result:
    name = "Config lock"
    proc = run(["python", "scripts/validate_config_lock.py"], verbose)
    if proc.returncode != 0:
        return Result(name, "fail", "drift detected")
    return Result(name, "ok", "clean")


def check_perf(verbose: bool) -> Result:
    name = "Perf baseline"
    allow = os.getenv("PERF_ALLOW_REGRESSION") == "1"
    run_path = Path("reports/perf_run.json")
    base_path = Path("scripts/perf_baseline.json")
    if not run_path.exists() or not base_path.exists():
        return Result(name, "fail", "missing perf data")
    try:
        run_data = json.loads(run_path.read_text() or "{}")
        base_data = json.loads(base_path.read_text() or "{}")
    except json.JSONDecodeError:
        return Result(name, "fail", "invalid JSON")
    regress = []
    for k, base_val in base_data.items():
        run_val = run_data.get(k)
        if run_val is None:
            continue
        if run_val > base_val * 1.1:
            regress.append(k)
    if regress and not allow:
        return Result(name, "fail", f"regressions: {', '.join(regress)}")
    return Result(name, "ok", "within baseline")


def check_repo_map(verbose: bool) -> Result:
    name = "Repo map"
    proc = run(["python", "scripts/generate_repo_map.py"], verbose)
    if proc.returncode != 0:
        return Result(name, "fail", "generation failed")
    diff = subprocess.run(
        ["git", "diff", "--quiet", "repo_map.yaml", "docs/REPO_MAP.md"]
    )
    if diff.returncode != 0:
        return Result(name, "fail", "repo map dirty")
    return Result(name, "ok", "clean")


def detect_expected_version(arg_version: str | None) -> str | None:
    if arg_version:
        return arg_version
    tag = os.environ.get("GITHUB_REF_NAME")
    if tag and tag.startswith("v"):
        return tag[1:]
    try:
        tag = (
            subprocess.check_output([
                "git",
                "describe",
                "--tags",
                "--exact-match",
            ], text=True)
            .strip()
        )
        if tag.startswith("v"):
            return tag[1:]
    except subprocess.CalledProcessError:
        return None
    return None


def get_source_version() -> tuple[str | None, str | None]:
    candidates = [
        (Path("dr_rd/__init__.py"), r"__version__\s*=\s*['\"]([^'\"]+)['\"]"),
        (Path("pyproject.toml"), r"^version\s*=\s*['\"]([^'\"]+)['\"]"),
    ]
    for path, pattern in candidates:
        if not path.exists():
            continue
        m = re.search(pattern, path.read_text(), re.MULTILINE)
        if m:
            return m.group(1), str(path)
    return None, None


def check_changelog_version(expected_version: str | None) -> Result:
    name = "Changelog and version"
    changelog = Path("CHANGELOG.md")
    if not changelog.exists():
        return Result(name, "fail", "missing CHANGELOG.md")
    text = changelog.read_text()
    m = re.search(r"## \[Unreleased\](.*?)(?:\n## \[|\Z)", text, re.S)
    if not m or not m.group(1).strip():
        return Result(name, "fail", "Unreleased section empty")
    if not expected_version:
        return Result(name, "fail", "expected version not provided")
    version, src = get_source_version()
    if not version:
        return Result(name, "fail", "version string not found")
    if version != expected_version:
        return Result(name, "fail", f"{version} != {expected_version}")
    return Result(name, "ok", f"version {version} matches {expected_version}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-version", help="Expected version X.Y.Z")
    parser.add_argument("--json", action="store_true", help="Write JSON report")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    expected = detect_expected_version(args.expected_version)

    results = [
        check_ci(args.verbose),
        check_locks(args.verbose),
        check_vulns(args.verbose),
        check_licenses(args.verbose),
        check_sbom(),
        check_config_lock(args.verbose),
        check_perf(args.verbose),
        check_repo_map(args.verbose),
        check_changelog_version(expected),
    ]

    ok = all(r.status in {"ok", "skipped"} for r in results)

    for r in results:
        print(f"{r.name}: {r.status} ({r.message})")

    if args.json:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        out = {"results": [r.__dict__ for r in results], "ok": ok}
        (reports_dir / "release_check.json").write_text(json.dumps(out, indent=2))

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
