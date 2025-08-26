"""Utilities for reading and patching repository files."""
from __future__ import annotations

from pathlib import Path
import fnmatch
import subprocess
import yaml
from typing import List, Dict

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
SECRET_PATHS_FILE = CONFIG_DIR / "secret_paths.yaml"

DEFAULT_DENY = [
    ".git/**",
    "node_modules/**",
    "env/**",
    "__pycache__/**",
    "*.pyc",
    "*.pyo",
    "*.exe",
    "*.dll",
    "*.so",
    "*.dylib",
]
ALLOW_EXTS = {".py", ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".cfg"}

try:
    with open(SECRET_PATHS_FILE, "r", encoding="utf-8") as fh:
        EXTRA_DENY = yaml.safe_load(fh) or []
except FileNotFoundError:
    EXTRA_DENY = []

DENY_PATTERNS = set(DEFAULT_DENY + EXTRA_DENY)


def _is_denied(rel_path: Path) -> bool:
    p = rel_path.as_posix()
    return any(fnmatch.fnmatch(p, pattern) for pattern in DENY_PATTERNS)


def _is_allowed(rel_path: Path) -> bool:
    return rel_path.suffix in ALLOW_EXTS and not _is_denied(rel_path)


def read_repo(globs: List[str]) -> List[Dict[str, str]]:
    """Read files matching the provided globs."""
    results: List[Dict[str, str]] = []
    for pattern in globs:
        for file in ROOT.glob(pattern):
            if not file.is_file():
                continue
            rel = file.relative_to(ROOT)
            if not _is_allowed(rel):
                continue
            try:
                text = file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            results.append({"path": str(rel), "text": text})
    return results


def plan_patch(diff_spec: str) -> str:
    return diff_spec


def apply_patch(diff: str, dry_run: bool = True) -> Dict[str, str]:
    """Validate or apply a unified diff."""
    files = set()
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            files.add(line[6:])
    for f in files:
        rel = Path(f)
        if not _is_allowed(rel):
            raise ValueError(f"Path not allowed: {f}")
    cmd = ["patch", "-p0", "--binary"]
    if dry_run:
        cmd.append("--dry-run")
    try:
        proc = subprocess.run(
            cmd,
            input=diff.encode(),
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return {"status": "error", "message": "patch utility not found"}
    if proc.returncode != 0:
        return {"status": "error", "message": proc.stderr.decode()}
    return {"status": "validated" if dry_run else "applied"}


def summarize_diff(diff: str) -> Dict[str, object]:
    """Return a summary of a unified diff."""

    files: Dict[str, Dict[str, int]] = {}
    current: Dict[str, int] | None = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            current = files.setdefault(path, {"path": path, "adds": 0, "dels": 0})
        elif line.startswith("+++ "):
            current = None
        elif line.startswith("+") and not line.startswith("+++"):
            if current:
                current["adds"] += 1
        elif line.startswith("-") and not line.startswith("---"):
            if current:
                current["dels"] += 1
    changed_files = len(files)
    additions = sum(f["adds"] for f in files.values())
    deletions = sum(f["dels"] for f in files.values())
    denied: List[str] = []
    ok: List[str] = []
    for path in files:
        if _is_allowed(Path(path)):
            ok.append(path)
        else:
            denied.append(path)
    return {
        "changed_files": changed_files,
        "additions": additions,
        "deletions": deletions,
        "files": list(files.values()),
        "denied": denied,
        "ok": ok,
    }


def within_patch_limits(diff: str, max_files: int, max_bytes: int) -> bool:
    """Check patch against file and byte caps."""

    summary = summarize_diff(diff)
    if summary["changed_files"] > max_files:
        return False
    if len(diff.encode("utf-8")) > max_bytes:
        return False
    return True
