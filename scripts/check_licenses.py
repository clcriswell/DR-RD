#!/usr/bin/env python3
"""Check third-party licenses against the project policy."""
import argparse
import json
import subprocess
import sys
from importlib.metadata import distributions
from pathlib import Path

from packaging.requirements import Requirement

ALLOW = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "MPL-2.0"}
WARN = {
    "LGPL-2.1",
    "LGPL-2.1-only",
    "LGPL-2.1-or-later",
    "LGPL-3.0",
    "LGPL-3.0-only",
    "LGPL-3.0-or-later",
    "EPL-2.0",
}
DENY = {
    "AGPL-3.0",
    "AGPL-3.0-only",
    "AGPL-3.0-or-later",
    "GPL-3.0",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
}


def build_parent_map() -> dict[str, set[str]]:
    """Map each package to the distributions that require it."""
    parents: dict[str, set[str]] = {}
    for dist in distributions():
        for req_str in dist.requires or []:
            try:
                req = Requirement(req_str)
            except Exception:
                continue
            name = req.name.lower()
            parents.setdefault(name, set()).add(dist.metadata.get("Name", dist.name))
    return parents


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Path to pip-licenses JSON output")
    args = parser.parse_args()

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    out_path = reports_dir / "licenses.json"

    if args.input:
        data = json.loads(Path(args.input).read_text() or "[]")
    else:
        result = subprocess.run(
            ["pip-licenses", "--format=json"],
            capture_output=True,
            text=True,
            check=False,
        )
        data = json.loads(result.stdout or "[]")
    out_path.write_text(json.dumps(data, indent=2))

    parents = build_parent_map()
    offenders = []
    for pkg in data:
        license_name = (pkg.get("License") or "").strip()
        pkg_name = pkg.get("Name")
        if license_name in DENY:
            offenders.append((pkg_name, license_name, sorted(parents.get(pkg_name.lower(), []))))
        elif license_name in WARN:
            print(f"WARN: {pkg_name} uses {license_name} license")

    if offenders:
        print("Denied licenses found:")
        for name, lic, parents_list in offenders:
            if parents_list:
                print(f"  {name} ({lic}) required by {', '.join(parents_list)}")
            else:
                print(f"  {name} ({lic})")
        return 1

    print("No denied licenses found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
