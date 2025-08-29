#!/usr/bin/env python
import json
import sys
from pathlib import Path

FIXTURE = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "connectors" / "fda_search.json"
)


def _load():
    if FIXTURE.exists():
        return json.loads(FIXTURE.read_text())
    return {"results": [{"id": "demo"}]}


def main() -> int:
    data = _load()
    out = {"scenario": "dynamic", "sources": data.get("results", [])}
    if not out["sources"]:
        return 1
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
