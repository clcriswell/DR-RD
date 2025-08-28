#!/usr/bin/env python
import json
import sys
from pathlib import Path

FIXTURE = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "connectors" / "uspto_search.json"
)


def main() -> int:
    data = json.loads(FIXTURE.read_text())
    out = {"scenario": "specialists", "sources": data.get("results", [])}
    if not out["sources"]:
        return 1
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
