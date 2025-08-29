#!/usr/bin/env python3
"""Gate pip-audit results, failing on high or critical vulnerabilities."""
import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]


def load_vulnerabilities(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text() or "[]")
    except Exception:
        return []
    if isinstance(data, dict) and "vulnerabilities" in data:
        return data.get("vulnerabilities", [])
    if isinstance(data, list):
        return data
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to pip-audit JSON report")
    args = parser.parse_args()

    vulns = load_vulnerabilities(Path(args.input))
    counts: Counter[str] = Counter()
    high_or_crit = False
    for item in vulns:
        sev = str(item.get("severity", "UNKNOWN")).upper()
        counts[sev] += 1
        if sev in {"HIGH", "CRITICAL"}:
            high_or_crit = True

    print("Vulnerability summary:")
    for sev in SEVERITY_ORDER:
        if counts[sev]:
            print(f"  {sev}: {counts[sev]}")

    if high_or_crit and os.environ.get("AUDIT_ALLOW_HIGH") != "1":
        print("High or critical vulnerabilities found. Set AUDIT_ALLOW_HIGH=1 to override.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
