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


def _load():
    if FIXTURE.exists():
        return json.loads(FIXTURE.read_text())
    return {"results": [{"id": "demo"}]}


def main() -> int:
    data = _load()
    sources = data.get("results") or data.get("data", [])
    out = {
        "scenario": "rag",
        "modes": {
            "LIGHT": {"sources": sources},
            "AGGRESSIVE": {"sources": sources},
        },
    }
    if not out["modes"]["LIGHT"]["sources"] or not out["modes"]["AGGRESSIVE"]["sources"]:
        return 1
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
