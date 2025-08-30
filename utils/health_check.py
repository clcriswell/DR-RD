from __future__ import annotations

import importlib.metadata as importlib_metadata
import json
import os
import platform
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib as toml  # type: ignore
except Exception:  # pragma: no cover
    try:
        import tomli as toml  # type: ignore
    except Exception:  # pragma: no cover
        toml = None  # type: ignore


DR_DIR = Path(".dr_rd")
TELEMETRY_DIR = DR_DIR / "telemetry"
RUNS_DIR = DR_DIR / "runs"
REPO_MAP_PATH = Path("repo_map.yaml")


@dataclass(frozen=True)
class CheckResult:
    id: str
    name: str
    status: str  # "pass" | "warn" | "fail"
    details: str
    remedy: str
    duration_ms: int


@dataclass(frozen=True)
class HealthReport:
    summary: dict[str, int]
    checks: list[CheckResult]
    env: dict[str, Any]


def _time_it(func):
    def wrapper() -> CheckResult:
        start = time.time()
        res = func()
        duration_ms = int((time.time() - start) * 1000)
        return CheckResult(
            id=res[0],
            name=res[1],
            status=res[2],
            details=res[3],
            remedy=res[4],
            duration_ms=duration_ms,
        )

    return wrapper


@_time_it
def _check_python() -> tuple[str, str, str, str, str]:
    version_ok = sys.version_info >= (3, 10)
    packages = ["streamlit", "requests", "pandas", "numpy"]
    missing: list[str] = []
    versions: dict[str, str | None] = {}
    for p in packages:
        try:
            versions[p] = importlib_metadata.version(p)
        except importlib_metadata.PackageNotFoundError:
            missing.append(p)
            versions[p] = None
    details = (
        f"python {platform.python_version()}"
        + ", "
        + ", ".join(f"{k}:{v}" for k, v in versions.items())
    )
    if not version_ok or missing:
        status = "warn"
        remedy = "Update Python or install missing packages"
    else:
        status = "pass"
        remedy = ""
    return (
        "python",
        "Python & packages",
        status,
        details,
        remedy,
    )


@_time_it
def _check_theme() -> tuple[str, str, str, str, str]:
    config_path = Path(".streamlit/config.toml")
    if not config_path.exists():
        return (
            "theme",
            "Theme config",
            "warn",
            "Missing .streamlit/config.toml",
            "Add theme config",
        )
    if toml is None:
        return (
            "theme",
            "Theme config",
            "warn",
            "toml parser unavailable",
            "Install tomllib/tomli",
        )
    try:
        data = toml.loads(config_path.read_text(encoding="utf-8"))
    except Exception as e:
        return (
            "theme",
            "Theme config",
            "warn",
            f"Invalid TOML: {e}",
            "Fix config.toml",
        )
    theme = data.get("theme", {})
    allowed = {
        "primaryColor",
        "backgroundColor",
        "secondaryBackgroundColor",
        "textColor",
        "font",
    }
    invalid = [k for k in theme.keys() if k not in allowed]
    if invalid:
        return (
            "theme",
            "Theme config",
            "warn",
            f"Invalid keys: {', '.join(invalid)}",
            "Remove invalid theme keys",
        )
    return (
        "theme",
        "Theme config",
        "pass",
        "Theme config valid",
        "",
    )


@_time_it
def _check_filesystem() -> tuple[str, str, str, str, str]:
    try:
        DR_DIR.mkdir(exist_ok=True)
        TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        for p in [DR_DIR, TELEMETRY_DIR, RUNS_DIR]:
            if not os.access(p, os.W_OK):
                raise PermissionError(f"{p} not writable")
        free = shutil.disk_usage(DR_DIR).free
        if free < 100 * 1024 * 1024:
            status = "warn"
            details = f"Free disk {free}B"
            remedy = "Free up disk space"
        else:
            tmp = DR_DIR / "tmp_health.txt"
            tmp.write_text("ping", encoding="utf-8")
            _ = tmp.read_text(encoding="utf-8")
            tmp.unlink()
            status = "pass"
            details = "Directories writable"
            remedy = ""
    except Exception as e:
        status = "fail"
        details = str(e)
        remedy = "Ensure .dr_rd directories exist and are writable"
    return (
        "filesystem",
        "Filesystem",
        status,
        details,
        remedy,
    )


@_time_it
def _check_telemetry() -> tuple[str, str, str, str, str]:
    path = TELEMETRY_DIR / "health_probe.jsonl"
    try:
        TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write("{}\n")
        path.unlink()
        return (
            "telemetry",
            "Telemetry write",
            "pass",
            "Telemetry directory writable",
            "",
        )
    except Exception as e:
        return (
            "telemetry",
            "Telemetry write",
            "fail",
            str(e),
            "Check telemetry directory permissions",
        )


@_time_it
def _check_secrets() -> tuple[str, str, str, str, str]:
    secret = os.environ.get("gcp_service_account")
    if not secret:
        secrets_path = Path(".streamlit/secrets.toml")
        if secrets_path.exists() and toml is not None:
            try:
                data = toml.loads(secrets_path.read_text(encoding="utf-8"))
                secret = data.get("gcp_service_account")
            except Exception:
                pass
    if not secret:
        return (
            "secrets",
            "GCP service account",
            "warn",
            "gcp_service_account missing",
            "Set gcp_service_account in env or secrets",
        )
    try:
        json.loads(secret)
        return (
            "secrets",
            "GCP service account",
            "pass",
            "gcp_service_account present",
            "",
        )
    except Exception as e:
        return (
            "secrets",
            "GCP service account",
            "fail",
            f"Invalid JSON: {e}",
            "Provide valid JSON",
        )


@_time_it
def _check_network() -> tuple[str, str, str, str, str]:
    if os.getenv("NO_NET") == "1":
        return (
            "network",
            "Network reachability",
            "warn",
            "NO_NET=1",
            "Unset NO_NET to enable network tests",
        )
    import requests

    urls = ["https://api.openai.com", "https://www.google.com"]
    failures: list[str] = []
    for u in urls:
        try:
            r = requests.head(u, timeout=2)
            if r.status_code >= 400:
                failures.append(u)
        except Exception:
            failures.append(u)
    if failures:
        return (
            "network",
            "Network reachability",
            "warn",
            ", ".join(failures),
            "Check network connectivity",
        )
    return (
        "network",
        "Network reachability",
        "pass",
        "All endpoints reachable",
        "",
    )


@_time_it
def _check_repo_map() -> tuple[str, str, str, str, str]:
    if not REPO_MAP_PATH.exists():
        return (
            "repo_map",
            "Repo map",
            "warn",
            "repo_map.yaml missing",
            "Run scripts/generate_repo_map.py",
        )
    try:
        REPO_MAP_PATH.read_text(encoding="utf-8")
        return (
            "repo_map",
            "Repo map",
            "pass",
            "repo_map.yaml present",
            "",
        )
    except Exception as e:
        return (
            "repo_map",
            "Repo map",
            "warn",
            str(e),
            "Ensure repo_map.yaml readable",
        )


CHECKS = [
    _check_python,
    _check_theme,
    _check_filesystem,
    _check_telemetry,
    _check_secrets,
    _check_network,
    _check_repo_map,
]


def env_summary() -> dict[str, Any]:
    packages = {}
    for p in ["streamlit", "requests", "pandas", "numpy"]:
        try:
            packages[p] = importlib_metadata.version(p)
        except importlib_metadata.PackageNotFoundError:
            packages[p] = None
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": packages,
    }


def run_all() -> HealthReport:
    checks = [func() for func in CHECKS]
    summary: dict[str, int] = {}
    for c in checks:
        summary[c.status] = summary.get(c.status, 0) + 1
    return HealthReport(summary=summary, checks=checks, env=env_summary())


def to_markdown(report: HealthReport) -> str:
    lines = ["| id | status | name | remedy |", "| --- | --- | --- | --- |"]
    for c in report.checks:
        lines.append(f"| {c.id} | {c.status} | {c.name} | {c.remedy} |")
    return "\n".join(lines)


def to_json(report: HealthReport) -> bytes:
    from dataclasses import asdict

    return json.dumps(asdict(report), ensure_ascii=False).encode("utf-8")
