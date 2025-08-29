#!/usr/bin/env python3
"""Generate SBOMs for the project.

Creates CycloneDX SBOMs for the current Python environment and, when possible,
for the repository filesystem using Syft. Outputs are written to the ``sbom/``
directory and overwritten on each run.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
import sys

SBOM_DIR = Path("sbom")
PYTHON_SBOM = SBOM_DIR / "cyclonedx-python.json"
REPO_SBOM = SBOM_DIR / "cyclonedx-repo.json"


def _component_count(path: Path) -> str:
    try:
        with path.open() as fh:
            data = json.load(fh)
        return str(len(data.get("components", [])))
    except Exception:
        return "unknown"


def main() -> int:
    SBOM_DIR.mkdir(exist_ok=True)

    cmd = ["cyclonedx-bom", "-o", str(PYTHON_SBOM)]
    if shutil.which("cyclonedx-bom") is None:
        cmd = ["cyclonedx-py", "environment", "-o", str(PYTHON_SBOM)]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        return result.returncode

    components_py = _component_count(PYTHON_SBOM)

    syft = shutil.which("syft")
    components_repo = None
    if syft:
        repo_result = subprocess.run([
            syft,
            "dir:.",
            "-o",
            f"cyclonedx-json={REPO_SBOM}",
        ])
        if repo_result.returncode == 0:
            components_repo = _component_count(REPO_SBOM)
        else:
            print("Syft failed, skipping repo SBOM", file=sys.stderr)
    else:
        print("Syft not installed; skipping repo SBOM", file=sys.stderr)

    print(f"Python SBOM: {PYTHON_SBOM} ({components_py} components)")
    if REPO_SBOM.exists():
        comp = components_repo or "unknown"
        print(f"Repo SBOM: {REPO_SBOM} ({comp} components)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
