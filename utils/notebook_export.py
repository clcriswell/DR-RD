"""Notebook export helpers."""

from __future__ import annotations

import json
import platform
from typing import Mapping, Sequence, Optional, Tuple

import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

from .redaction import redact_public


def build_notebook(
    run_id: str,
    meta: Mapping,
    lock: Mapping,
    rows: Sequence[Mapping],
    artifacts: Sequence[Tuple[str, str]] | None = None,
    *,
    include_small_artifacts: bool = True,
    max_embed_bytes: int = 200_000,
) -> bytes:
    """Return UTF‑8 encoded ``.ipynb`` bytes."""

    nb = new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3"}
    nb.metadata["language_info"] = {
        "name": "python",
        "version": platform.python_version(),
    }

    started = meta.get("started_at")
    completed = meta.get("completed_at")
    status = meta.get("status")
    mode = meta.get("mode")
    title = f"# DR RD Run {run_id}\n\nStarted: {started}\n\nCompleted: {completed}\n\nStatus: {status}\n\nMode: {mode}"
    nb.cells.append(new_markdown_cell(title))

    repro = ["## Reproduction info"]
    provider = lock.get("provider") or lock.get("model")
    if provider:
        repro.append(f"- Provider/model: {provider}")
    budgets = lock.get("budgets")
    if budgets:
        repro.append(f"- Budgets: {json.dumps(budgets)}")
    repro.append("- Warning: prompts and outputs are redacted for public sharing.")
    nb.cells.append(new_markdown_cell("\n".join(repro)))

    cfg_json = json.dumps(lock, ensure_ascii=False, indent=2)
    cfg_json = redact_public(cfg_json)
    nb.cells.append(new_code_cell(cfg_json, metadata={"name": "config"}))

    for row in rows:
        phase = row.get("phase")
        name = row.get("name")
        status = row.get("status")
        dur = row.get("duration_ms")
        header = f"## [{phase}] {name} ({status}, {dur} ms)"
        nb.cells.append(new_markdown_cell(header))

        if row.get("prompt"):
            nb.cells.append(
                new_markdown_cell("### Prompt\n" + redact_public(str(row.get("prompt"))))
            )
        if row.get("summary"):
            nb.cells.append(
                new_markdown_cell("### Output\n" + redact_public(str(row.get("summary"))))
            )
        cites = row.get("citations") or []
        if cites:
            lines = ["### Citations"]
            for c in cites:
                if isinstance(c, Mapping):
                    cid = c.get("id")
                    snip = c.get("snippet") or c.get("text")
                    lines.append(f"- {cid}: {redact_public(str(snip))}")
            nb.cells.append(new_markdown_cell("\n".join(lines)))

    totals = {
        "tokens": meta.get("tokens") or 0,
        "cost_usd": meta.get("cost_usd") or 0.0,
        "duration_s": meta.get("duration_ms", 0) / 1000,
    }
    lines = ["## Totals"]
    lines.append(f"- Tokens: {totals['tokens']}")
    lines.append(f"- Cost USD: {totals['cost_usd']}")
    lines.append(f"- Duration s: {totals['duration_s']}")
    nb.cells.append(new_markdown_cell("\n".join(lines)))

    return nbformat.writes(nb).encode("utf-8")


__all__ = ["build_notebook"]

