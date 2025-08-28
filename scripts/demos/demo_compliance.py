#!/usr/bin/env python
import json
import sys
from pathlib import Path

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "connectors"
    / "regulations_search.json"
)


def main() -> int:
    data = json.loads(FIXTURE.read_text())
    sources = data.get("results") or data.get("data", [])
    out = {"scenario": "compliance", "sources": sources}
    if not out["sources"]:
        return 1
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
