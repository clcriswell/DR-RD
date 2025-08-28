#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from dr_rd.kb import store, index
from dr_rd.examples import harvest, catalog


def main() -> None:
    store.compact()
    idx_stats = index.rebuild()
    records = store.query({}, limit=0)
    examples = harvest(records)
    catalog.refresh(examples)
    report = {
        "records": len(records),
        "examples": len(examples),
        "index": idx_stats,
    }
    Path("distill_report.md").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    main()
